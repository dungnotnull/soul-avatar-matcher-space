from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BigFiveScores(_message.Message):
    __slots__ = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
    OPENNESS_FIELD_NUMBER: _ClassVar[int]
    CONSCIENTIOUSNESS_FIELD_NUMBER: _ClassVar[int]
    EXTRAVERSION_FIELD_NUMBER: _ClassVar[int]
    AGREEABLENESS_FIELD_NUMBER: _ClassVar[int]
    NEUROTICISM_FIELD_NUMBER: _ClassVar[int]
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    def __init__(self, openness: _Optional[float] = ..., conscientiousness: _Optional[float] = ..., extraversion: _Optional[float] = ..., agreeableness: _Optional[float] = ..., neuroticism: _Optional[float] = ...) -> None: ...

class EmotionDistribution(_message.Message):
    __slots__ = ("joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral")
    JOY_FIELD_NUMBER: _ClassVar[int]
    SADNESS_FIELD_NUMBER: _ClassVar[int]
    ANGER_FIELD_NUMBER: _ClassVar[int]
    FEAR_FIELD_NUMBER: _ClassVar[int]
    SURPRISE_FIELD_NUMBER: _ClassVar[int]
    DISGUST_FIELD_NUMBER: _ClassVar[int]
    NEUTRAL_FIELD_NUMBER: _ClassVar[int]
    joy: float
    sadness: float
    anger: float
    fear: float
    surprise: float
    disgust: float
    neutral: float
    def __init__(self, joy: _Optional[float] = ..., sadness: _Optional[float] = ..., anger: _Optional[float] = ..., fear: _Optional[float] = ..., surprise: _Optional[float] = ..., disgust: _Optional[float] = ..., neutral: _Optional[float] = ...) -> None: ...

class PersonalityVector(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, values: _Optional[_Iterable[float]] = ...) -> None: ...

class BehavioralFingerprint(_message.Message):
    __slots__ = ("hash", "window_count", "last_updated")
    HASH_FIELD_NUMBER: _ClassVar[int]
    WINDOW_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATED_FIELD_NUMBER: _ClassVar[int]
    hash: bytes
    window_count: int
    last_updated: int
    def __init__(self, hash: _Optional[bytes] = ..., window_count: _Optional[int] = ..., last_updated: _Optional[int] = ...) -> None: ...

class AvatarCapsule(_message.Message):
    __slots__ = ("avatar_id", "vector", "big_five", "avg_emotion", "fingerprint", "slm_endpoint", "created_at", "drift_delta")
    AVATAR_ID_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    BIG_FIVE_FIELD_NUMBER: _ClassVar[int]
    AVG_EMOTION_FIELD_NUMBER: _ClassVar[int]
    FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    SLM_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    DRIFT_DELTA_FIELD_NUMBER: _ClassVar[int]
    avatar_id: str
    vector: PersonalityVector
    big_five: BigFiveScores
    avg_emotion: EmotionDistribution
    fingerprint: BehavioralFingerprint
    slm_endpoint: str
    created_at: int
    drift_delta: float
    def __init__(self, avatar_id: _Optional[str] = ..., vector: _Optional[_Union[PersonalityVector, _Mapping]] = ..., big_five: _Optional[_Union[BigFiveScores, _Mapping]] = ..., avg_emotion: _Optional[_Union[EmotionDistribution, _Mapping]] = ..., fingerprint: _Optional[_Union[BehavioralFingerprint, _Mapping]] = ..., slm_endpoint: _Optional[str] = ..., created_at: _Optional[int] = ..., drift_delta: _Optional[float] = ...) -> None: ...

class PendingMatch(_message.Message):
    __slots__ = ("match_id", "self_capsule", "other_capsule", "compatibility_score", "anonymized_report", "self_confirmed", "other_confirmed", "created_at", "expires_at")
    MATCH_ID_FIELD_NUMBER: _ClassVar[int]
    SELF_CAPSULE_FIELD_NUMBER: _ClassVar[int]
    OTHER_CAPSULE_FIELD_NUMBER: _ClassVar[int]
    COMPATIBILITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    ANONYMIZED_REPORT_FIELD_NUMBER: _ClassVar[int]
    SELF_CONFIRMED_FIELD_NUMBER: _ClassVar[int]
    OTHER_CONFIRMED_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    match_id: str
    self_capsule: AvatarCapsule
    other_capsule: AvatarCapsule
    compatibility_score: float
    anonymized_report: str
    self_confirmed: bool
    other_confirmed: bool
    created_at: int
    expires_at: int
    def __init__(self, match_id: _Optional[str] = ..., self_capsule: _Optional[_Union[AvatarCapsule, _Mapping]] = ..., other_capsule: _Optional[_Union[AvatarCapsule, _Mapping]] = ..., compatibility_score: _Optional[float] = ..., anonymized_report: _Optional[str] = ..., self_confirmed: _Optional[bool] = ..., other_confirmed: _Optional[bool] = ..., created_at: _Optional[int] = ..., expires_at: _Optional[int] = ...) -> None: ...
