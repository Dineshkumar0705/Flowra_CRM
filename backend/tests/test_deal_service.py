"""Tests for DealService business logic."""

import uuid
import pytest

from app.models.deal import DealStage, DealPriority
from app.schemas.deal import DealCreate, DealUpdate, DealFilters
from app.services.deal_service import DealService
from app.core.exceptions import NotFoundError


@pytest.fixture()
def ws_and_user(make_user, make_workspace):
    user = make_user()
    ws = make_workspace(owner_id=user.id)
    return user, ws


class TestDealCreate:
    def test_create_basic_deal(self, db, ws_and_user):
        user, ws = ws_and_user
        svc = DealService(db, ws.id)

        deal = svc.create(DealCreate(
            title="Landing page for Acme",
            value=75000,
            currency="INR",
        ), created_by=user.id)

        assert deal.id is not None
        assert deal.workspace_id == ws.id
        assert deal.title == "Landing page for Acme"
        assert deal.value == 75000
        assert deal.stage == DealStage.NEW

    def test_deal_gets_ai_score(self, db, ws_and_user):
        user, ws = ws_and_user
        svc = DealService(db, ws.id)
        deal = svc.create(DealCreate(title="Scored deal", value=100000), created_by=user.id)
        assert 0 <= deal.ai_score <= 100


class TestDealList:
    def test_list_returns_only_workspace_deals(self, db, make_user, make_workspace):
        user = make_user()
        ws1 = make_workspace(owner_id=user.id, name="WS1")
        ws2 = make_workspace(owner_id=user.id, name="WS2")

        svc1 = DealService(db, ws1.id)
        svc2 = DealService(db, ws2.id)

        svc1.create(DealCreate(title="Deal A", value=10000))
        svc1.create(DealCreate(title="Deal B", value=20000))
        svc2.create(DealCreate(title="Deal C", value=30000))

        items1, total1 = svc1.list(DealFilters())
        items2, total2 = svc2.list(DealFilters())

        assert total1 == 2
        assert total2 == 1

    def test_filter_by_stage(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        make_deal(ws.id, stage=DealStage.NEW)
        make_deal(ws.id, stage=DealStage.NEW)
        make_deal(ws.id, stage=DealStage.WON)

        svc = DealService(db, ws.id)
        items, total = svc.list(DealFilters(stage=DealStage.NEW))
        assert total == 2

    def test_pagination(self, db, ws_and_user):
        user, ws = ws_and_user
        svc = DealService(db, ws.id)
        for i in range(5):
            svc.create(DealCreate(title=f"Deal {i}", value=i * 1000))

        page1, total = svc.list(DealFilters(), page=1, per_page=2)
        page2, _ = svc.list(DealFilters(), page=2, per_page=2)

        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestDealUpdate:
    def test_update_value(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        deal = make_deal(ws.id, value=50000)
        svc = DealService(db, ws.id)

        updated = svc.update(deal.id, DealUpdate(value=75000))
        assert updated.value == 75000

    def test_update_nonexistent_raises(self, db, ws_and_user):
        user, ws = ws_and_user
        svc = DealService(db, ws.id)
        with pytest.raises(NotFoundError):
            svc.update(str(uuid.uuid4()), DealUpdate(value=1))


class TestDealStageMove:
    def test_move_to_new_stage(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        deal = make_deal(ws.id, stage=DealStage.NEW)
        svc = DealService(db, ws.id)

        moved = svc.move_stage(deal.id, DealStage.CONTACTED)
        assert moved.stage == DealStage.CONTACTED

    def test_move_to_won_sets_won_at(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        deal = make_deal(ws.id, stage=DealStage.NEGOTIATION)
        svc = DealService(db, ws.id)

        won = svc.move_stage(deal.id, DealStage.WON)
        assert won.won_at is not None
        assert won.stage == DealStage.WON

    def test_move_to_lost_sets_lost_at(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        deal = make_deal(ws.id)
        svc = DealService(db, ws.id)

        lost = svc.move_stage(deal.id, DealStage.LOST)
        assert lost.lost_at is not None


class TestDealDelete:
    def test_soft_delete(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        deal = make_deal(ws.id)
        svc = DealService(db, ws.id)

        svc.delete(deal.id)
        result = svc.get(deal.id)
        assert result is None

    def test_deleted_deal_not_in_list(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        d1 = make_deal(ws.id)
        d2 = make_deal(ws.id)
        svc = DealService(db, ws.id)
        svc.delete(d1.id)

        items, total = svc.list(DealFilters())
        assert total == 1
        assert items[0].id == d2.id


class TestDealDashboard:
    def test_dashboard_returns_summary(self, db, ws_and_user, make_deal):
        user, ws = ws_and_user
        make_deal(ws.id, value=100000)
        make_deal(ws.id, value=50000, stage=DealStage.WON)

        svc = DealService(db, ws.id)
        dashboard = svc.get_dashboard()

        assert "total_deals" in dashboard
        assert "pipeline_value" in dashboard
        assert dashboard["total_deals"] >= 2
