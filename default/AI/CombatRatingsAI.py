import freeOrionAIInterface as fo  # pylint: disable=import-error
import FleetUtilsAI
from EnumsAI import MissionType
from freeorion_tools import get_ai_tag_grade, dict_to_tuple, tuple_to_dict
from ShipDesignAI import get_part_type

piloting_grades = {}


def get_empire_standard_fighter():
    stats_dict = {}
    for fleet_id in FleetUtilsAI.get_empire_fleet_ids_by_role(MissionType.MILITARY):
        ship_stats = FleetCombatStats(fleet_id, consider_refuel=True).get_ship_combat_stats()
        for this_stats in ship_stats:
            stats_tuple = this_stats.get_stats(hashable=True)
            stats_dict[stats_tuple] = stats_dict.get(stats_tuple, 0) + 1
    if stats_dict:
        standard_fighter_stats = sorted([(v, k) for k, v in stats_dict.items()])[-1][1]
        return ShipCombatStats(stats=standard_fighter_stats)
    else:
        return default_ship_stats()


def default_ship_stats():
    attacks = (4.0, 1)
    structure = 15
    shields = 0
    fighters = 0
    launchrate = 0
    fighter_damage = 0
    return ShipCombatStats(stats=(attacks, structure, shields, fighters, launchrate, fighter_damage))


class ShipCombatStats(object):
    """Stores all relevant stats of a ship for combat strength evaluation."""
    class BasicStats(object):
        def __init__(self, stat_tuple=None, attacks=None, structure=1, shields=0):
            """

            :param stat_tuple:
             :type stat_tuple: tuple|None
            :param attacks:
            :type attacks: dict|None
            :param structure:
            :type structure: int
            :param shields:
            :type shields: int
            :return:
            """
            if stat_tuple and isinstance(stat_tuple, tuple):
                attack_tuple, self.structure, self.shields = stat_tuple
                self.attacks = tuple_to_dict(attack_tuple)
            else:
                self.structure = structure
                self.shields = shields
                self.attacks = attacks or {}

        def get_stats(self, hashable=False):
            if not hashable:
                return self.attacks, self.structure, self.shields
            else:
                return dict_to_tuple(self.attacks), self.structure, self.shields

        def __str__(self):
            return str(self.get_stats())

    class FighterStats(object):
        def __init__(self, stat_tuple=None, capacity=0, launch_rate=0, damage=0):
            if stat_tuple and isinstance(stat_tuple, tuple):
                self.capacity, self.launch_rate, self.damage = stat_tuple
            else:
                self.capacity = capacity
                self.launch_rate = launch_rate
                self.damage = damage

        def __str__(self):
            return str(self.get_stats())

        def get_stats(self):
            return self.capacity, self.launch_rate, self.damage

    def __init__(self, ship_id=-1, consider_refuel=False, stats=None):
        self.__ship_id = ship_id
        self._consider_refuel = consider_refuel
        if stats:
            print stats
            self._basic_stats = self.BasicStats(stats[0:3])  # TODO: Should probably determine size dynamically
            self._fighter_stats = self.FighterStats(stats[3:])
        else:
            self._basic_stats = self.BasicStats()
            self._fighter_stats = self.FighterStats()
            self.__get_stats_from_ship()

    def __str__(self):
        return str(self.get_stats())

    def __get_stats_from_ship(self):
        """Read and store combat related stats from ship"""
        universe = fo.getUniverse()
        ship = universe.getShip(self.__ship_id)
        if not ship:
            return  # TODO: Add some estimate for stealthed ships

        if self._consider_refuel:
            structure = ship.currentMeterValue(fo.meterType.maxStructure)
            shields = ship.currentMeterValue(fo.meterType.maxShield)
        else:
            structure = ship.currentMeterValue(fo.meterType.structure)
            shields = ship.currentMeterValue(fo.meterType.shield)
        attacks = {}
        fighter_launchrate = 0
        fighter_capacity = 0
        fighter_damage = 0
        design = ship.design
        if design and ship.isArmed:
            meter_choice = fo.meterType.maxCapacity if self._consider_refuel else fo.meterType.capacity
            for partname in design.parts:
                if not partname:
                    continue
                pc = get_part_type(partname).partClass
                if pc == fo.shipPartClass.shortRange:
                    damage = ship.currentPartMeterValue(meter_choice, partname)
                    attacks[damage] = attacks.get(damage, 0) + 1
                elif pc == fo.shipPartClass.fighterBay:
                    fighter_launchrate += ship.currentPartMeterValue(fo.meterType.capacity, partname)
                elif pc == fo.shipPartClass.fighterHangar:
                    fighter_capacity += ship.currentPartMeterValue(meter_choice, partname)
                    part_damage = ship.currentPartMeterValue(fo.meterType.secondaryStat, partname)
                    if part_damage != fighter_damage and fighter_damage > 0:
                        # the C++ code fails also in this regard, so FOCS content *should* not allow this.
                        # TODO: Depending on future implementation, might actually need to handle this case.
                        print "WARNING: Multiple hangar types present on one ship, estimatates expected to be wrong."
                    fighter_damage = max(fighter_damage, part_damage)
        self._basic_stats = self.BasicStats(structure=structure, shields=shields, attacks=attacks)
        self._fighter_stats = self.FighterStats(fighter_capacity, fighter_launchrate, fighter_damage)

    def get_basic_stats(self, hashable=False):
        return self._basic_stats.get_stats(hashable=hashable)

    def get_fighter_stats(self):
        return self._fighter_stats.get_stats()

    def get_rating(self, enemy_stats=None):
        # adjust base stats according to enemy stats
        my_attacks, my_structure, my_shields = self.get_basic_stats()
        e_avg_attack = 1
        if enemy_stats:
            e_attacks, e_structure, e_shields = enemy_stats.get_basic_stats()
            if e_attacks:
                e_num_attacks = sum(n for n in e_attacks.values())
                e_total_attack = sum(n*dmg for dmg, n in e_attacks.iteritems())
                e_avg_attack = e_total_attack / e_num_attacks
                e_net_attack = sum(n*max(dmg - my_shields, .001) for dmg, n in e_attacks.iteritems())
                e_net_attack = max(e_net_attack, .1*e_total_attack)
                shield_factor = e_total_attack / e_net_attack
                my_structure *= max(1, shield_factor)
            my_total_attack = sum(n*max(dmg - e_shields, .001) for dmg, n in my_attacks.iteritems())
        else:
            my_total_attack = sum(n*dmg for dmg, n in my_attacks.iteritems())
            my_structure += my_shields

        # consider fighter attacks
        capacity, launchrate, fighter_damage = self.get_fighter_stats()
        launched_1st_bout = min(capacity, launchrate)
        launched_2nd_bout = min(max(capacity - launchrate, 0), launchrate)
        survival_rate = .2  # chance of a fighter launched in bout 1 to live in turn 3 TODO Actual estimation
        total_fighter_damage = fighter_damage * (launched_1st_bout * (1+survival_rate) + launched_2nd_bout)
        fighter_damage_per_bout = total_fighter_damage / 3
        my_total_attack += fighter_damage_per_bout

        # consider fighter protection factor
        fighters_shot_down = (1-survival_rate**2) * launched_1st_bout + (1-survival_rate) * launched_2nd_bout
        damage_prevented = fighters_shot_down * e_avg_attack
        my_structure += damage_prevented

        return my_total_attack * my_structure

    def get_stats(self, hashable=False):
        return self.get_basic_stats(hashable=hashable)+self.get_fighter_stats()


class FleetCombatStats(object):

    def __init__(self, fleet_id=-1, consider_refuel=False):
        self.__fleet_id = fleet_id
        self._consider_refuel = consider_refuel
        self.__ship_stats = []
        self.__get_stats_from_fleet()

    def get_ship_stats(self, hashable=False):
        return map(lambda x: x.get_stats(hashable=hashable), self.__ship_stats)

    def get_ship_combat_stats(self):
        return list(self.__ship_stats)

    def get_rating(self, enemy_stats=None):
        return combine_ratings_list(map(lambda x: x.get_rating(enemy_stats), self.__ship_stats))

    def __get_stats_from_fleet(self):
        universe = fo.getUniverse()
        fleet = universe.getFleet(self.__fleet_id)
        if not fleet:
            return
        for ship_id in fleet.shipIDs:
            self.__ship_stats.append(ShipCombatStats(ship_id, self._consider_refuel))


def get_fleet_rating(fleet_id, enemy_stats=None):
    return FleetCombatStats(fleet_id, consider_refuel=False).get_rating(enemy_stats)


def get_piloting_grades(species_name):
    if species_name not in piloting_grades:
        spec_tags = []
        if species_name:
            species = fo.getSpecies(species_name)
            if species:
                spec_tags = species.tags
            else:
                print "Error: get_piloting_grades couldn't retrieve species '%s'" % species_name
        piloting_grades[species_name] = (get_ai_tag_grade(spec_tags, 'WEAPONS'),
                                         get_ai_tag_grade(spec_tags, 'SHIELDS'),
                                         get_ai_tag_grade(spec_tags, 'ATTACKTROOPS'),
                                         )
    return piloting_grades[species_name]


def weight_attack_troops(troops, grade):
    """Re-weights troops on a ship based on species piloting grade.

    :type troops: float
    :type grade: str
    :return: piloting grade weighted troops
    :rtype: float
    """
    weight = {'NO': 0.0, 'BAD': 0.5, '': 1.0, 'GOOD': 1.5, 'GREAT': 2.0, 'ULTIMATE': 3.0}.get(grade, 1.0)
    return troops * weight


def weight_shields(shields, grade):
    """Re-weights shields based on species defense bonus."""
    offset = {'NO': 0, 'BAD': 0, '': 0, 'GOOD': 1.0, 'GREAT': 0, 'ULTIMATE': 0}.get(grade, 0)
    return shields + offset


def combine_ratings(rating1, rating2):
    return rating1 + rating2 + 2 * (rating1 * rating2)**0.5


def combine_ratings_list(ratings_list):
    return reduce(combine_ratings, ratings_list) if ratings_list else 0

