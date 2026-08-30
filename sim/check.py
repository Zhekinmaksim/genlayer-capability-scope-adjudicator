import importlib.util
import hashlib
import pathlib
import sys
import types


APPROVER = "0xaaa"
REQUESTER = "0xbbb"
THIRD = "0xccc"


class UserError(Exception):
    pass


class Address(str):
    def __new__(cls, value):
        return str.__new__(cls, str(value))


Address.ZERO = Address("0x0000000000000000000000000000000000000000")


class TreeMap(dict):
    @classmethod
    def __class_getitem__(cls, _item):
        return cls


class DynArray(list):
    @classmethod
    def __class_getitem__(cls, _item):
        return cls


class Keccak256:
    def __init__(self):
        self._h = hashlib.sha3_256()

    def update(self, data):
        self._h.update(data)

    def hexdigest(self):
        return self._h.hexdigest()


class Event:
    def emit(self):
        return None


def allow_storage(cls):
    return cls


class Public:
    def write(self, fn):
        return fn

    def view(self, fn):
        return fn


class Nondet:
    responses = []
    fail_next = False

    @classmethod
    def exec_prompt(cls, _prompt, **_kwargs):
        if cls.fail_next:
            cls.fail_next = False
            raise RuntimeError("provider down")
        if not cls.responses:
            raise RuntimeError("no response")
        return cls.responses.pop(0)


class EqPrinciple:
    @staticmethod
    def prompt_comparative(fn, _principle):
        return fn()


message = types.SimpleNamespace(sender_address=Address(APPROVER))
gl = types.SimpleNamespace(
    Contract=object,
    Event=Event,
    public=Public(),
    vm=types.SimpleNamespace(UserError=UserError),
    message=message,
    nondet=Nondet,
    eq_principle=EqPrinciple(),
)

genlayer = types.ModuleType("genlayer")
for name, value in {
    "Address": Address,
    "TreeMap": TreeMap,
    "DynArray": DynArray,
    "Keccak256": Keccak256,
    "allow_storage": allow_storage,
    "u32": int,
    "gl": gl,
}.items():
    setattr(genlayer, name, value)
sys.modules["genlayer"] = genlayer

root = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("contract", root / "contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


TIERS = "read only\nscoped write\ncustodial"
CAPS = "read logs\nedit profile\ntransfer treasury"


def fresh():
    scope = contract.CapabilityScopeAdjudicator()
    scope.scopes = TreeMap()
    scope.ids = DynArray()
    Nondet.responses = []
    Nondet.fail_next = False
    message.sender_address = Address(APPROVER)
    return scope


def must_raise(fn, code):
    try:
        fn()
    except UserError as exc:
        assert str(exc) == code, f"expected {code}, got {exc}"
        return
    raise AssertionError(f"expected {code}")


def tier_response(tiers):
    return {
        "capabilities": [
            {"tier": int(tier), "why": f"tier {tier}"}
            for tier in tiers
        ]
    }


def open_and_request(scope, policy="allow\nreview\ndeny", sid="case"):
    scope.open_scope(sid, REQUESTER, TIERS, policy)
    purpose = "operate support agent"
    digest = contract._digest(purpose + "\n" + CAPS)
    message.sender_address = Address(REQUESTER)
    scope.submit_request(sid, purpose, CAPS, digest)
    message.sender_address = Address(THIRD)


def case_1_denied_by_committed_policy():
    scope = fresh()
    open_and_request(scope)
    Nondet.responses.append(tier_response("012"))
    assert scope.evaluate("case") == "DENIED"
    assert scope.assignment("case") == "012"
    assert scope.denied_capabilities("case") == ["transfer treasury"]
    assert scope.review_capabilities("case") == ["edit profile"]
    assert len(scope.classified("case")) == 3


def case_2_same_tiers_different_policy():
    scope = fresh()
    open_and_request(scope, "allow\nallow\nreview")
    Nondet.responses.append(tier_response("012"))
    assert scope.evaluate("case") == "REVIEW_REQUIRED"
    assert scope.denied_capabilities("case") == []
    assert scope.review_capabilities("case") == ["transfer treasury"]


def case_3_fully_granted():
    scope = fresh()
    open_and_request(scope)
    Nondet.responses.append(tier_response("000"))
    assert scope.evaluate("case") == "GRANTED"
    assert scope.denied_capabilities("case") == []
    assert scope.review_capabilities("case") == []


def case_4_bad_tier_and_provider_failure():
    scope = fresh()
    open_and_request(scope)
    Nondet.responses.append({"capabilities": [{"tier": 7}, {"tier": 0}, {"tier": 0}]})
    assert scope.evaluate("case") == "UNDETERMINED"
    assert scope.reason_of("case") == "TIER_OUT_OF_RANGE"

    scope = fresh()
    open_and_request(scope)
    Nondet.fail_next = True
    assert scope.evaluate("case") == "UNDETERMINED"
    assert scope.reason_of("case") == "JUDGMENT_UNAVAILABLE"


def case_5_identity_and_ordering():
    scope = fresh()
    scope.open_scope("case", REQUESTER, TIERS, "allow\nreview\ndeny")
    purpose = "operate support agent"
    digest = contract._digest(purpose + "\n" + CAPS)
    must_raise(lambda: scope.submit_request("case", purpose, CAPS, digest), "NOT_REQUESTER")
    message.sender_address = Address(THIRD)
    must_raise(lambda: scope.submit_request("case", purpose, CAPS, digest), "NOT_REQUESTER")
    message.sender_address = Address(REQUESTER)
    must_raise(lambda: scope.submit_request("case", purpose, CAPS, "0x00"), "HASH_MISMATCH")
    message.sender_address = Address(THIRD)
    must_raise(lambda: scope.evaluate("case"), "NOT_REQUESTED_OR_SETTLED")


def case_6_one_shot_and_terminal():
    scope = fresh()
    open_and_request(scope)
    message.sender_address = Address(REQUESTER)
    must_raise(
        lambda: scope.submit_request("case", "new", "read logs", contract._digest("new\nread logs")),
        "ALREADY_REQUESTED_OR_CLOSED",
    )
    message.sender_address = Address(APPROVER)
    must_raise(lambda: scope.close("case"), "ALREADY_REQUESTED_OR_CLOSED")
    message.sender_address = Address(THIRD)
    Nondet.responses.append('{"capabilities":[{"tier":0},{"tier":0},{"tier":0}]}')
    assert scope.evaluate("case") == "GRANTED"
    must_raise(lambda: scope.evaluate("case"), "NOT_REQUESTED_OR_SETTLED")


def case_7_policy_and_taxonomy_guards():
    scope = fresh()
    must_raise(lambda: scope.open_scope("all", REQUESTER, TIERS, "allow\nallow\nallow"), "POLICY_ALLOWS_EVERYTHING")
    must_raise(lambda: scope.open_scope("count", REQUESTER, TIERS, "allow\ndeny"), "POLICY_COUNT_MISMATCH")
    must_raise(lambda: scope.open_scope("word", REQUESTER, TIERS, "allow\nmaybe\ndeny"), "UNKNOWN_DECISION")
    must_raise(lambda: scope.open_scope("few", REQUESTER, "only one", "deny"), "TOO_FEW_TIERS")
    must_raise(lambda: scope.open_scope("dup", REQUESTER, "read only\nREAD ONLY", "allow\ndeny"), "DUPLICATE_TIER")
    scope.open_scope("close", REQUESTER, TIERS, "allow\nreview\ndeny")
    assert scope.close("close") == "CLOSED"
    scope.open_scope("request", REQUESTER, TIERS, "allow\nreview\ndeny")
    message.sender_address = Address(REQUESTER)
    must_raise(lambda: scope.submit_request("request", " \n ", CAPS, "0x00"), "EMPTY_PURPOSE")
    must_raise(
        lambda: scope.submit_request("request", "purpose", "read logs\nREAD LOGS", "0x00"),
        "DUPLICATE_CAPABILITY",
    )


cases = [
    case_1_denied_by_committed_policy,
    case_2_same_tiers_different_policy,
    case_3_fully_granted,
    case_4_bad_tier_and_provider_failure,
    case_5_identity_and_ordering,
    case_6_one_shot_and_terminal,
    case_7_policy_and_taxonomy_guards,
]

for case in cases:
    case()
    print(f"PASS {case.__name__}")

print(f"{len(cases)}/{len(cases)} pass")
