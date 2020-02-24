from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from ark.types import PrimalItem
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.asset import UAsset
from ue.proxy import UEProxyStructure

from .items.cooking import convert_cooking_values
from .items.crafting import convert_crafting_values
from .items.durability import convert_durability_values
from .items.egg import convert_egg_values
from .items.status import convert_status_effect
from .items.structure import gather_structure_values
from .items.weapon import gather_weapon_values

__all__ = [
    'ItemsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class ItemsStage(JsonHierarchyExportStage):
    def get_skip(self):
        return not self.manager.config.export_wiki.ExportItems

    def get_format_version(self) -> str:
        return "1"

    def get_field(self) -> str:
        return "items"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalItem.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        item: PrimalItem = cast(PrimalItem, proxy)

        v: Dict[str, Any] = dict()
        if not item.has_override('DescriptiveNameBase'):
            return None
        v['index'] = -1
        v['name'] = item.get('DescriptiveNameBase', 0, None)
        v['description'] = item.get('ItemDescription', 0, None)
        v['blueprintPath'] = item.get_source().fullname

        icon = item.get('ItemIcon', 0, None)
        if not icon:
            return None  # this is used as an indicator that this is a non-spawnable base item
        v['icon'] = icon

        itemType = item.get('MyItemType', 0, None)
        v['type'] = itemType.get_enum_value_name()

        if v['type'] == 'MiscConsumable':
            consumableType = item.get('MyConsumableType', 0, None)
            v['type'] += '/' + consumableType.get_enum_value_name()
        elif v['type'] == 'Equipment':
            equipmentType = item.get('MyEquipmentType', 0, None)
            v['type'] += '/' + equipmentType.get_enum_value_name()

        if item.has_override('bPreventCheatGive'):
            v['preventCheatGive'] = item.bPreventCheatGive[0]

        if item.has_override('DefaultFolderPaths'):
            v['folders'] = [str(folder) for folder in item.DefaultFolderPaths[0].values]
        else:
            v['folders'] = []

        v['weight'] = item.BaseItemWeight[0]
        v['maxQuantity'] = item.MaxItemQuantity[0]

        if item.has_override('SpoilingTime'):
            v['spoilage'] = dict(time=item.SpoilingTime[0])
            if item.has_override('SpoilingItem'):
                v['spoilage']['productBP'] = item.SpoilingItem[0]

        if item.bUseItemDurability[0].value:
            v.update(convert_durability_values(item))

        v.update(convert_crafting_values(item))
        v.update(gather_structure_values(item))
        v.update(gather_weapon_values(item))

        if item.has_override('UseItemAddCharacterStatusValues'):
            status_effects = item.UseItemAddCharacterStatusValues[0]
            v['statEffects'] = dict(convert_status_effect(entry) for entry in status_effects.values)

        if item.bIsEgg[0]:
            egg_data = convert_egg_values(item)
            if egg_data:
                v['egg'] = egg_data

        if item.bIsCookingIngredient[0]:
            v.update(convert_cooking_values(item))

        return v

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if not self.gathered_results:
            return None

        if not modid:
            # Add indices from the base PGD
            pgd_asset = self.manager.loader['/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP']
            self._add_pgd_indices(pgd_asset, None)
        else:
            for v in self.gathered_results:
                del v['index']

        return None

    def _add_pgd_indices(self, pgd_asset: UAsset, mod_data: Optional[Dict[str, Any]]):
        if not self.gathered_results or not pgd_asset.default_export or mod_data:
            return

        properties = pgd_asset.default_export.properties
        d = properties.get_property('MasterItemList', fallback=None)
        if not d:
            return

        master_list = []
        for ref in d.values:
            if ref.value.value:
                master_list.append(ref.value.value.fullname)

        for v in self.gathered_results:
            try:
                index = master_list.index(v['blueprintPath'])
                v['index'] = index
            except ValueError:
                del v['index']
