import avatar_pb2 as _avatar_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InitiateRequest(_message.Message):
    __slots__ = ("self_capsule", "peer_capsule", "topic_ids", "max_rounds_per_topic")
    SELF_CAPSULE_FIELD_NUMBER: _ClassVar[int]
    PEER_CAPSULE_FIELD_NUMBER: _ClassVar[int]
    TOPIC_IDS_FIELD_NUMBER: _ClassVar[int]
    MAX_ROUNDS_PER_TOPIC_FIELD_NUMBER: _ClassVar[int]
    self_capsule: _avatar_pb2.AvatarCapsule
    peer_capsule: _avatar_pb2.AvatarCapsule
    topic_ids: _containers.RepeatedScalarFieldContainer[str]
    max_rounds_per_topic: int
    def __init__(self, self_capsule: _Optional[_Union[_avatar_pb2.AvatarCapsule, _Mapping]] = ..., peer_capsule: _Optional[_Union[_avatar_pb2.AvatarCapsule, _Mapping]] = ..., topic_ids: _Optional[_Iterable[str]] = ..., max_rounds_per_topic: _Optional[int] = ...) -> None: ...

class InitiateResponse(_message.Message):
    __slots__ = ("session_id", "accepted", "message")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    accepted: bool
    message: str
    def __init__(self, session_id: _Optional[str] = ..., accepted: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class DebateTurn(_message.Message):
    __slots__ = ("session_id", "topic_id", "round", "speaker_avatar_id", "content", "is_final")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TOPIC_ID_FIELD_NUMBER: _ClassVar[int]
    ROUND_FIELD_NUMBER: _ClassVar[int]
    SPEAKER_AVATAR_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    topic_id: str
    round: int
    speaker_avatar_id: str
    content: str
    is_final: bool
    def __init__(self, session_id: _Optional[str] = ..., topic_id: _Optional[str] = ..., round: _Optional[int] = ..., speaker_avatar_id: _Optional[str] = ..., content: _Optional[str] = ..., is_final: _Optional[bool] = ...) -> None: ...

class MatchDecision(_message.Message):
    __slots__ = ("session_id", "avatar_id", "confirmed")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    AVATAR_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIRMED_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    avatar_id: str
    confirmed: bool
    def __init__(self, session_id: _Optional[str] = ..., avatar_id: _Optional[str] = ..., confirmed: _Optional[bool] = ...) -> None: ...

class MatchResult(_message.Message):
    __slots__ = ("session_id", "matched", "message", "compatibility_score")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    MATCHED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    COMPATIBILITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    matched: bool
    message: str
    compatibility_score: float
    def __init__(self, session_id: _Optional[str] = ..., matched: _Optional[bool] = ..., message: _Optional[str] = ..., compatibility_score: _Optional[float] = ...) -> None: ...
