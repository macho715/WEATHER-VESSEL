from wv.core.models import Route
from wv.core.repository import RouteRepository


def test_route_repository_get_and_register() -> None:
    repo = RouteRepository()
    mw4 = repo.get("MW4-AGI")
    assert mw4.name == "MW4-AGI"
    new_route = Route(name="TEST-1", points=[(1.0, 2.0)])
    repo.register(new_route)
    assert repo.get("test-1").points[0] == (1.0, 2.0)
    assert any(route.name == "TEST-1" for route in repo.list())
