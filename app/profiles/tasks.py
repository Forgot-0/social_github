from dataclasses import dataclass

from dishka.integrations.taskiq import FromDishka, inject
from app.core.services.storage.dtos import UploadFile
import magic
import pyvips

from app.core.events.service import BaseEventBus
from app.core.services.queues.task import BaseTask
from app.core.services.storage.service import StorageService
from app.profiles.config import profile_config
from app.profiles.events.avatars.uploaded import UploadedAvatarsEvent


@dataclass
class AvatarUploadTask(BaseTask):
    __task_name__ = "avatar.uploaded"

    @staticmethod
    @inject
    async def run(
        user_id: int,
        key_base: str,
        storage_service: FromDishka[StorageService],
        event_bus: FromDishka[BaseEventBus],
    ) -> None:
        sizes = [32, 64, 256, 512]
        original_key = f"{key_base}/original"
        data = await storage_service.download(profile_config.AVATAR_BUCKET,original_key)
        mime = magic.from_buffer(data, mime=True)

        if not mime.startswith('image/'):
            raise 

        img: pyvips.Image = pyvips.Image.new_from_buffer(data, '', access='sequential') # type: ignore
        versions = {}

        for s in sizes:
            thumb = img.thumbnail_image(s, height=s) # type: ignore

            webp = thumb.write_to_buffer('.webp') # type: ignore
            avif = thumb.write_to_buffer('.avif') # type: ignore
            jpg = thumb.write_to_buffer('.jpg') # type: ignore

            key_webp = f"{key_base}/{s}.webp"
            key_avif = f"{key_base}/{s}.avif"
            key_jpg = f"{key_base}/{s}.jpg"

            webp_url = await storage_service.upload_file(
                upload_file=UploadFile(
                    bucket_name=profile_config.AVATAR_BUCKET,
                    file_key=key_webp, file_content=webp, size=-1
                )
            )
            avif_url = await storage_service.upload_file(
                upload_file=UploadFile(
                    bucket_name=profile_config.AVATAR_BUCKET,
                    file_key=key_avif, file_content=avif, size=-1
                )
            )

            jpg_url = await storage_service.upload_file(
                upload_file=UploadFile(
                    bucket_name=profile_config.AVATAR_BUCKET,
                    file_key=key_jpg, file_content=jpg, size=-1
                )
            ) 

            versions[str(s)] = {"webp": webp_url, "avif": avif_url, "jpg": jpg_url}

            await event_bus.publish([
                UploadedAvatarsEvent(
                    user_id=user_id,
                    versions=versions
                )
            ])

    