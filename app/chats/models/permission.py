from enum import Enum, auto

from app.chats.models.chat_members import MemberRole


class Permission(Enum):
    SEND_MESSAGES = auto()
    DELETE_OWN_MSG = auto()
    DELETE_ANY_MSG = auto()
    EDIT_OWN_MSG = auto()
    PIN_MESSAGE = auto()

    ADD_MEMBERS = auto()
    REMOVE_MEMBERS = auto()
    BAN_MEMBERS = auto()
    CHANGE_ROLES = auto()

    EDIT_CHAT_INFO = auto()
    DELETE_CHAT = auto()

    READ_MESSAGES = auto()

 
ROLE_PERMISSIONS: dict[MemberRole, set[Permission]] = {
    MemberRole.VIEWER: {
        Permission.READ_MESSAGES,
    },
    MemberRole.MEMBER: {
        Permission.READ_MESSAGES,
        Permission.SEND_MESSAGES,
        Permission.EDIT_OWN_MSG,
        Permission.DELETE_OWN_MSG,
    },
    MemberRole.ADMIN: {
        Permission.READ_MESSAGES,
        Permission.SEND_MESSAGES,
        Permission.EDIT_OWN_MSG,
        Permission.DELETE_OWN_MSG,
        Permission.DELETE_ANY_MSG,
        Permission.PIN_MESSAGE,
        Permission.ADD_MEMBERS,
        Permission.REMOVE_MEMBERS,
        Permission.BAN_MEMBERS,
        Permission.EDIT_CHAT_INFO,
    },
    MemberRole.OWNER: {
        *list(Permission),
    },
}