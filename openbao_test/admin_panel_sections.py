"""Single source of truth for admin panel sections and secrets."""

SECTION_CONFIG = [
    {
        "id": "docs",
        "title": "Docs",
        "icon": "📄",
        "card_helper": "Document service credentials",
        "workspace_title": "Docs Secrets",
        "workspace_subtitle": "Manage document service secrets in a focused workspace.",
        "secrets": [
            {
                "id": "secret_1",
                "path": "editable/docs/test_1",
                "key": "test 1",
                "label": "test secret message",
            },
        ],
    },
    {
        "id": "drive",
        "title": "Drive",
        "icon": "🗂️",
        "card_helper": "Storage and file workflow credentials",
        "workspace_title": "Drive Secrets",
        "workspace_subtitle": "Manage storage and file workflow secrets in one place.",
        "secrets": [
            {
                "id": "secret_1",
                "path": "editable/drive/test",
                "key": "test 1",
                "label": "test secret message",
            },
        ],
    },
    {
        "id": "meet",
        "title": "Meet",
        "icon": "🎥",
        "card_helper": "Meeting platform integrations",
        "workspace_title": "Meet Secrets",
        "workspace_subtitle": "Manage meeting service secrets with clear section context.",
        "secrets": [
            {
                "id": "secret_1",
                "path": "editable/meet/test",
                "key": "test",
                "label": "test secret message",
            },
        ],
    },
    {
        "id": "message",
        "title": "Message",
        "icon": "💬",
        "card_helper": "Messaging channel service keys",
        "workspace_title": "Message Secrets",
        "workspace_subtitle": "Manage messaging service credentials and tokens.",
        "secrets": [
            {
                "id": "secret_1",
                "path": "editable/message/test",
                "key": "test",
                "label": "test secret message",
            },
        ],
    },
    {
        "id": "calendar",
        "title": "Calendar",
        "icon": "🗓️",
        "card_helper": "Calendar to plan and see scheduled meetings",
        "workspace_title": "Calendar Secrets",
        "workspace_subtitle": "Manage calendar service credentials and tokens.",
        "secrets": [
            {
                "id": "secret_1",
                "path": "editable/calander/test",
                "key": "test",
                "label": "this is for an ai api",
            },
        ],
    },
    {
        "id": "extra",
        "title": "Extra",
        "icon": "✨",
        "card_helper": "Root-level editable secrets only",
        "workspace_title": "Extra Secrets",
        "workspace_subtitle": "Manage root-level editable secrets under editable/.",
        "secrets": [
            {
                "id": "secret_1",
                "path": "editable/test",
                "key": "test",
                "label": "Test Secret",
            },
            {
                "id": "secret_2",
                "path": "editable/test_2",
                "key": "test 2",
                "label": "test secret 2",
            },
        ],
    },
]
