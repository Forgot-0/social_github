from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.chats.commands.attachments.request_upload import RequestAttachmentUploadCommand, UploadRequest
from app.chats.commands.messages.delete import DeleteMessageCommand
from app.chats.commands.messages.forward import ForwardMessageCommand, ForwardMessageResult
from app.chats.commands.messages.mark_read import MarkAsReadCommand
from app.chats.commands.messages.modify import EditMessageCommand
from app.chats.commands.messages.send import SendMessageCommand, SendMessageResult
from app.chats.dtos.attachments import AttachmentDownloadUrlDTO, UploadSlotDTO
from app.chats.dtos.messages import MessageCursorPage, MessageReadDetailsPageDTO
from app.chats.queries.attachments.get_url import GetAttachmentDownloadUrlQuery
from app.chats.queries.messages.get_detail import GetMessageReadDetailsQuery
from app.chats.queries.messages.get_list import GetMessagesQuery
from app.chats.schemas.messages.requests import (
    EditMessageRequest,
    ForwardMessageRequest,
    GetMessageReadDetailsRequest,
    GetMessagesRequest,
    MarkAsReadRequest,
    RequestAttachmentUploadRequest,
    SendMessageRequest,
)
from app.core.mediators.base import BaseMediator
from app.core.services.auth.depends import CurrentUserJWTData

router = APIRouter(route_class=DishkaRoute)



@router.post(
    "/upload",
    status_code=status.HTTP_200_OK,
    summary="Шаг 1: запросить presigned PUT URL(ы) для загрузки вложений",
    description=(
        "Если сообщение без медиа и/или файла то сразу ко второму шагу. "
        "Клиент указывает список файлов (имя, MIME, размер). "
        "Сервер возвращает upload_token и upload_url на каждый файл. "
        "Клиент загружает файл напрямую в S3 по upload_url (PUT), "
        "затем передаёт upload_token в `/messages/` (шаг 2)."
    ),
)
async def request_upload(
    chat_id: int,
    request: RequestAttachmentUploadRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> list[UploadSlotDTO]:
    results = await mediator.handle_command(
        RequestAttachmentUploadCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            uploads=[
                UploadRequest(
                    filename=u.filename,
                    mime_type=u.mime_type,
                    file_size=u.file_size,
                )
                for u in request.uploads
            ],
        )
    )
    return next(iter(results))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Шаг 2: отправить сообщение (с текстом и/или вложениями)",
    description=(
        "Передайте upload_tokens из /upload (после успешной загрузки в S3). "
        "Допустимо: до 10 медиа (image/video) и/или 1 файл. "
        "Контент и токены — взаимодополняемы; хотя бы одно должно быть указано."
    ),
)
async def send_message(
    chat_id: int,
    request: SendMessageRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> SendMessageResult:
    results = await mediator.handle_command(
        SendMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            content=request.content,
            reply_to_id=request.reply_to_id,
            message_type=request.message_type,
            upload_tokens=list(request.upload_tokens),
        )
    )
    return next(iter(results))

@router.post(
    "/forward",
    status_code=status.HTTP_201_CREATED,
    summary="Переслать сообщение в этот чат",
    description=(
        "Пересылает сообщение из source_chat_id в текущий чат. "
        "Пользователь должен быть членом обоих чатов. "
        "Вложения копируются по ссылке (S3 данные не дублируются)."
    ),
)
async def forward_message(
    chat_id: int,
    request: ForwardMessageRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> ForwardMessageResult:
    results = await mediator.handle_command(
        ForwardMessageCommand(
            user_jwt_data=user_jwt_data,
            source_chat_id=request.source_chat_id,
            source_message_id=request.source_message_id,
            target_chat_id=chat_id,
            comment=request.comment,
        )
    )
    return next(iter(results))


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Список сообщений (cursor-based), включает metadata вложений",
    description=(
        "Возвращает metadata вложений (id, тип, имя, размер) без presigned URL. "
        "Для получения URL скачивания используйте "
        "GET /{message_id}/attachments/{attachment_id}/url"
    ),
)
async def get_messages(
    chat_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
    params: GetMessagesRequest = Query(...),
) -> MessageCursorPage:
    return await mediator.handle_query(
        GetMessagesQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=params.limit,
            before_id=params.before_id,
        )
    )

@router.get(
    "/{message_id}/attachments/{attachment_id}/url",
    status_code=status.HTTP_200_OK,
    summary="Получить presigned URL для скачивания вложения (TTL 5 мин)",
    description=(
        "Доступно только членам чата. "
        "URL кешируется на сервере, повторные запросы не создают новый URL в S3."
    ),
)
async def get_attachment_download_url(
    chat_id: int,
    message_id: int,
    attachment_id: UUID,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> AttachmentDownloadUrlDTO:
    return await mediator.handle_query(
        GetAttachmentDownloadUrlQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            attachment_id=attachment_id,
        )
    )

@router.get(
    "/read-details",
    status_code=status.HTTP_200_OK,
    summary="Read-cursor детали по членам чата",
)
async def get_message_read_details(
    chat_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
    params: GetMessageReadDetailsRequest = Query(...),
) -> MessageReadDetailsPageDTO:
    return await mediator.handle_query(
        GetMessageReadDetailsQuery(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            limit=params.limit,
            after_user_id=params.after_user_id,
        )
    )

@router.put(
    "/{message_id}",
    status_code=status.HTTP_200_OK,
    summary="Редактировать своё сообщение",
)
async def edit_message(
    chat_id: int,
    message_id: int,
    request: EditMessageRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        EditMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
            new_content=request.content,
        )
    )


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete сообщения",
)
async def delete_message(
    chat_id: int,
    message_id: int,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        DeleteMessageCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=message_id,
        )
    )


@router.post(
    "/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отметить сообщения прочитанными",
)
async def mark_as_read(
    chat_id: int,
    request: MarkAsReadRequest,
    mediator: FromDishka[BaseMediator],
    user_jwt_data: CurrentUserJWTData,
) -> None:
    await mediator.handle_command(
        MarkAsReadCommand(
            user_jwt_data=user_jwt_data,
            chat_id=chat_id,
            message_id=request.message_id,
        )
    )
