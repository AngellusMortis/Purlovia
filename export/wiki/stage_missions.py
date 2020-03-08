from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from export.wiki.types import *
from ue.asset import UAsset
from ue.proxy import UEProxyStructure

from .stage_drops import decode_item_set

__all__ = [
    'MissionsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class MissionsStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "1"

    def get_name(self):
        return 'missions'

    def get_field(self) -> str:
        return "missions"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return MissionType.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        mission: MissionType = cast(MissionType, proxy)

        v: Dict[str, Any] = dict()
        v['bp'] = proxy.get_source().fullname
        v['type'] = 'base'
        v['name'] = mission.MissionDisplayName[0]
        v['description'] = mission.MissionDescription[0]

        v['targetPlayerLevel'] = mission.TargetPlayerLevel[0]
        v['maxPlayers'] = mission.MaxPlayerCount[0]
        v['maxDuration'] = mission.MissionMaxDurationSeconds[0]
        v['globalCooldown'] = mission.GlobalMissionCooldown[0]
        v['canBeRepeated'] = mission.bRepeatableMission[0]

        v.update(_get_more_values(mission))

        v['rewards'] = dict(
            hexagons=_convert_hexagon_values(mission),
            items=_convert_item_rewards(mission),
        )

        return v


def _get_more_values(mission: MissionType):
    v: Dict[str, Any] = dict()

    if isinstance(mission, MissionType_Retrieve):
        retrieval = cast(MissionType_Retrieve, mission)
        v['type'] = 'retrieve'

        v['retrieval'] = dict(item=retrieval.get('RetrieveItemClass', fallback=None))
    elif isinstance(mission, MissionType_Retrieve):
        escort = cast(MissionType_Escort, mission)
        v['type'] = 'escort'

        v['escort'] = dict(
            targetWalkSpeed=escort.EscortDinoBaseWalkSpeed[0],
            targetEscortedSpeed=escort.EscortDinoEscortedSpeed[0],
        )
    elif isinstance(mission, MissionType_Hunt):
        _hunt = cast(MissionType_Hunt, mission)
        v['type'] = 'hunt'

    return v


def _convert_item_rewards(mission: MissionType):
    d = mission.get('CustomItemSets', fallback=None)
    v = list()

    if d:
        for itemset in d.values:
            v.append(decode_item_set(itemset))

    return dict(
        qtyScale=(mission.MinItemSets[0], mission.MaxItemSets[0]),
        sets=v,
    )


def _convert_hexagon_values(mission: MissionType) -> Dict[str, Any]:
    v: Dict[str, Any] = dict()

    v['totalQty'] = mission.HexagonsOnCompletion[0]
    if mission.bDivideHexogonsOnCompletion[0]:
        v['divideByPlayers'] = True

    return v
