"""
Taylor Signs-McMurtry
April 30, 2026
Final Project, 20 Questions Edition 2.0

My Description:
A 20 Questions game that uses trait-based elimination engine to guess what the player is thinking of. 
The game supports multiple catergories, sound effects, dark mode, and a 
large knowledgable database. 

Requirements: Python 3.14+  |  pip install pygame numpy  (optional, for sound) 
use pip install pygame--ce if pip install pygame will not let you install pygame.
Run: python main.py
"""

import tkinter as tk
import math, random, threading, time
from collections import defaultdict

# ── Optional pygame sound ─────────────────────────────────────────────────────
try:
    import pygame, numpy as np
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
#  SOUND ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class SoundEngine:
    def __init__(self):
        self.enabled = SOUND_AVAILABLE

    def _tone(self, freq, dur, vol=0.18, wave="sine"):
        if not SOUND_AVAILABLE: return None
        n = int(44100 * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        if   wave == "sine":     w = np.sin(2*math.pi*freq*t)
        elif wave == "triangle": w = 2*np.abs(2*(t*freq - np.floor(t*freq+0.5)))-1
        elif wave == "sawtooth": w = 2*(t*freq - np.floor(t*freq+0.5))
        else:                    w = np.sign(np.sin(2*math.pi*freq*t))
        w = (w * np.linspace(1,0,n)**1.5 * vol * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack((w,w)))

    def _seq(self, notes):
        if not self.enabled: return
        def _run():
            for freq,dur,wave,delay in notes:
                if delay: time.sleep(delay)
                s = self._tone(freq,dur,wave=wave)
                if s: s.play()
                time.sleep(dur*0.5)
        threading.Thread(target=_run, daemon=True).start()

    def play_start(self):    self._seq([(392,.15,"triangle",0),(523,.15,"triangle",0),(659,.15,"triangle",0),(784,.25,"triangle",0)])
    def play_question(self): self._seq([(660,.18,"sine",0),(880,.12,"sine",.05)])
    def play_yes(self):      self._seq([(523,.10,"triangle",0),(659,.10,"triangle",0)])
    def play_no(self):       self._seq([(330,.10,"sawtooth",0),(293,.10,"sawtooth",0)])
    def play_guess(self):    self._seq([(f,.18,"triangle",0) for f in [523,587,659,698,784]])
    def play_win(self):      self._seq([(f,.22,"triangle",0) for f in [523,659,784,1047,784,1047]])
    def play_lose(self):     self._seq([(f,.20,"sawtooth",0) for f in [440,415,392,349]])
    def play_click(self):    self._seq([(880,.07,"sine",0)])
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


# ══════════════════════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE
#  Each answer is a dict of trait -> True/False/None (None = not applicable)
#  Questions are the keys; values are True/False for that answer.
# ══════════════════════════════════════════════════════════════════════════════

# ── Question text lookup ──────────────────────────────────────────────────────
QUESTIONS = {
    # Category
    "is_animal":       "Is it an animal?",
    "is_plant":        "Is it a plant?",
    "is_food":         "Is it a food or drink?",
    "is_object":       "Is it a physical object (not alive)?",
    "is_place":        "Is it a place (city, country, landmark, etc.)?",
    "is_element":      "Is it a chemical element?",
    "is_person":       "Is it a real person (living or historical)?",
    "is_character":    "Is it a fictional character?",
    "is_fungus":       "Is it a fungus (like a mushroom)?", #Added fungus for FUNgus!

    # Animal traits
    "animal_mammal":   "Is it a mammal?",
    "animal_bird":     "Is it a bird?",
    "animal_fish":     "Is it a fish?",
    "animal_reptile":  "Is it a reptile?",
    "animal_insect":   "Is it an insect or bug?",
    "animal_water":    "Does it live in water?",
    "animal_fly":      "Can it fly?",
    "animal_pet":      "Is it commonly kept as a pet?",
    "animal_large":    "Is it larger than a dog?",
    "animal_africa":   "Is it native to Africa?",
    "animal_australia":"Is it native to Australia?",
    "animal_danger":   "Is it considered dangerous to humans?",
    "animal_domestic": "Is it a domesticated animal?",
    "animal_4legs":    "Does it have four legs?",
    "animal_stripes":  "Does it have stripes or spots?",
    "animal_swim":     "Is it a strong swimmer?",
    "animal_nocturnal":"Is it nocturnal?",
    "animal_cold":     "Is it cold-blooded?",
    "animal_fur":      "Does it have fur or hair?",
    "animal_ocean":    "Does it live in the ocean?",
    "animal_predator": "Is it a predator?",
    "animal_horn":     "Does it have horns, tusks, or a trunk?",
    "animal_shell":    "Does it have a shell?",
    "animal_venom":    "Is it venomous or poisonous?",
    "animal_eggs":     "Does it lay eggs?",
    "animal_tiny":     "Is it smaller than a cat?",
    "animal_popular":  "Is it a very well-known animal?",

    # Plant traits
    "plant_tree":      "Is it a tree?",
    "plant_flower":    "Is it a flower?",
    "plant_edible":    "Is it edible?",
    "plant_indoor":    "Can it be kept indoors?",
    "plant_tall":      "Can it grow taller than a person?",
    "plant_fruit":     "Does it produce fruit?",
    "plant_needles":   "Does it have needles instead of leaves?",
    "plant_colorful":  "Is it known for being colorful?",
    "plant_fragrant":  "Is it fragrant?",
    "plant_water":     "Does it grow in or near water?",
    "plant_desert":    "Does it grow in dry or desert conditions?",
    "plant_garden":    "Is it commonly found in gardens?",
    "plant_prickly":   "Is it prickly or thorny?",

    # Food traits
    "food_drink":      "Is it a drink?",
    "food_sweet":      "Is it sweet?",
    "food_hot":        "Is it usually served hot?",
    "food_meat":       "Does it contain meat?",
    "food_fruit_item": "Is it a fruit?",
    "food_veg":        "Is it a vegetable?",
    "food_baked":      "Is it baked?",
    "food_dairy":      "Is it a dairy product?",
    "food_alcohol":    "Is it alcoholic?",
    "food_fast":       "Is it a fast food item?",
    "food_italian":    "Is it an Italian dish?",
    "food_breakfast":  "Is it commonly eaten for breakfast?",
    "food_snack":      "Is it a snack?",
    "food_frozen":     "Is it served cold or frozen?",
    "food_fizzy":      "Is it fizzy?",
    "food_caffeine":   "Does it contain caffeine?",
    "food_yellow":      "Is it yellow?",

    # Object traits
    "obj_electronic":  "Is it electronic?",
    "obj_screen":      "Does it have a screen?",
    "obj_portable":    "Is it portable / handheld?",
    "obj_furniture":   "Is it furniture?",
    "obj_kitchen":     "Is it used in the kitchen?",
    "obj_writing":     "Is it used for writing?",
    "obj_clothing":    "Is it clothing or worn on the body?",
    "obj_battery":     "Does it run on a battery?",
    "obj_school":      "Is it commonly used at school?",
    "obj_transport":   "Is it used for transport?",
    "obj_music":       "Is it related to music?",
    "obj_sport":       "Is it used in sport?",
    "obj_bedroom":     "Is it typically found in a bedroom?",
    "obj_carry":       "Is it used to carry things?",
    "obj_cutting":     "Does it have a blade or sharp edge?",
    "obj_modern":      "Is it a modern invention (after 1900)?",
    "obj_metal":       "Is it made primarily of metal?",

    # Place traits
    "place_country":   "Is it a country?",
    "place_city":      "Is it a city?",
    "place_landmark":  "Is it a famous landmark or building?",
    "place_natural":   "Is it a natural feature (mountain, river, etc.)?",
    "place_europe":    "Is it in Europe?",
    "place_asia":      "Is it in Asia?",
    "place_americas":  "Is it in the Americas?",
    "place_africa":    "Is it in Africa?",
    "place_ocean_area":"Is it in or near an ocean?",
    "place_ancient":   "Is it known for ancient history?",
    "place_large":     "Is it one of the largest of its kind in the world?",
    "place_capital":   "Is it a capital city?",
    "place_cold":      "Is it known for cold weather?",
    "place_hot":       "Is it known for hot weather?",
    "place_island":    "Is it an island or island nation?",
    "place_tourist":   "Is it a major tourist destination?",

    # Element traits
    "elem_metal":      "Is it a metal?",
    "elem_precious":   "Is it a precious metal (gold, silver, platinum)?",
    "elem_gas_rt":     "Is it a gas at room temperature?",
    "elem_liquid_rt":  "Is it a liquid at room temperature?",
    "elem_common":     "Is it one of the most common elements on Earth?",
    "elem_magnetic":   "Is it magnetic?",
    "elem_conduct":    "Is it a good conductor of electricity?",
    "elem_toxic":      "Is it toxic or dangerous?",
    "elem_life":       "Is it essential for life?",
    "elem_breathe":    "Is it found in the air we breathe?",
    "elem_jewellery":  "Is it used in jewellery?",
    "elem_light":      "Is it a very lightweight element?",

    # Person traits
    "person_historical":"Was this person born before 1900?",
    "person_scientist": "Are they known as a scientist or inventor?",
    "person_leader":    "Are they known as a political leader?",
    "person_artist":    "Are they known as an artist, musician, or writer?",
    "person_athlete":   "Are they known as an athlete or sportsperson?",
    "person_male":      "Is this person male?",
    "person_american":  "Are they American?",
    "person_european":  "Are they European?",
    "person_alive":     "Are they still alive today?",
    "person_famous":    "Are they world-famous?",
    "person_20c":       "Did they live or rise to fame in the 20th century?",

    # Character traits
    "char_book":        "Is this character from a book?",
    "char_film":        "Is this character from a film or TV show?",
    "char_game":        "Is this character from a video game?",
    "char_hero":        "Is this character a hero or protagonist?",
    "char_villain":     "Is this character a villain?",
    "char_superhero":   "Is this character a superhero?",
    "char_animated":    "Is this character animated (cartoon)?",
    "char_human":       "Does this character appear human?",
    "char_animal_char": "Is this character an animal?",
    "char_magic":       "Does this character use magic or special powers?",
    "char_child":       "Is this character a child or young person?",
    "char_famous_story":"Is this character from a very famous story?",

    # Extra trait labels used by the database
    "animal_small":    "Is it a small animal?",
    "animal_prickly":  "Is it prickly or spiky?",
    "obj_tiny":        "Is it very small?",
    "place_modern":    "Is it known for being modern?",
}

# ── Answer database ───────────────────────────────────────────────────────────
# Format: "Answer Name": { trait_key: True/False, ... }
# Omitted traits are treated as unknown/not-applicable during scoring.

ANSWERS = {

    # ── ANIMALS ──────────────────────────────────────────────────────────────
    "Dog": {
        "is_animal":True,"animal_mammal":True,"animal_pet":True,"animal_domestic":True,
        "animal_fur":True,"animal_4legs":True,"animal_large":False,"animal_tiny":False,
        "animal_predator":False,"animal_water":False,"animal_fly":False,"animal_popular":True,
    },
    "Cat": {
        "is_animal":True,"animal_mammal":True,"animal_pet":True,"animal_domestic":True,
        "animal_fur":True,"animal_4legs":True,"animal_large":False,"animal_tiny":False,
        "animal_nocturnal":True,"animal_predator":True,"animal_fly":False,"animal_popular":True,
    },
    "Rabbit": {
        "is_animal":True,"animal_mammal":True,"animal_pet":True,"animal_domestic":True,
        "animal_fur":True,"animal_4legs":True,"animal_large":False,"animal_tiny":False,
        "animal_fly":False,"animal_water":False,
    },
    "Hamster": {
        "is_animal":True,"animal_mammal":True,"animal_pet":True,"animal_tiny":True,
        "animal_fur":True,"animal_4legs":True,"animal_nocturnal":True,"animal_fly":False,
    },
    "Goldfish": {
        "is_animal":True,"animal_fish":True,"animal_pet":True,"animal_water":True,
        "animal_cold":True,"animal_swim":True,"animal_tiny":True,"animal_fly":False,
    },
    "Parrot": {
        "is_animal":True,"animal_bird":True,"animal_pet":True,"animal_fly":True,
        "animal_4legs":False,"animal_popular":True,
    },
    "Horse": {
        "is_animal":True,"animal_mammal":True,"animal_domestic":True,"animal_large":True,
        "animal_4legs":True,"animal_fur":True,"animal_fly":False,"animal_popular":True,
    },
    "Cow": {
        "is_animal":True,"animal_mammal":True,"animal_domestic":True,"animal_large":True,
        "animal_4legs":True,"animal_fur":True,"animal_fly":False,
    },
    "Pig": {
        "is_animal":True,"animal_mammal":True,"animal_domestic":True,"animal_4legs":True,
        "animal_fur":False,"animal_large":False,"animal_fly":False,
    },
    "Chicken": {
        "is_animal":True,"animal_bird":True,"animal_domestic":True,"animal_fly":False,
        "animal_eggs":True,"animal_4legs":False,
    },
    "Elephant": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_horn":True,"animal_fur":False,"animal_fly":False,
        "animal_popular":True,"animal_predator":False,
    },
    "Lion": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_predator":True,"animal_fur":True,"animal_fly":False,
        "animal_popular":True,"animal_danger":True,
    },
    "Tiger": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_stripes":True,"animal_predator":True,"animal_fur":True,"animal_fly":False,
        "animal_popular":True,"animal_danger":True,
    },
    "Giraffe": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_fly":False,"animal_predator":False,"animal_stripes":True,
        "animal_popular":True,
    },
    "Zebra": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_stripes":True,"animal_fly":False,"animal_predator":False,
    },
    "Cheetah": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_stripes":True,"animal_predator":True,"animal_fly":False,
    },
    "Leopard": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_stripes":True,"animal_predator":True,"animal_fly":False,
        "animal_nocturnal":True,
    },
    "Hippo": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_africa":True,"animal_water":True,"animal_danger":True,"animal_fly":False,
        "animal_swim":True,
    },
    "Gorilla": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_africa":True,
        "animal_fly":False,"animal_fur":True,"animal_danger":True,"animal_4legs":False,
        "animal_popular":True,
    },
    "Chimpanzee": {
        "is_animal":True,"animal_mammal":True,"animal_africa":True,"animal_fly":False,
        "animal_fur":True,"animal_4legs":False,"animal_popular":True,
    },
    "Kangaroo": {
        "is_animal":True,"animal_mammal":True,"animal_australia":True,"animal_large":True,
        "animal_4legs":True,"animal_fur":True,"animal_fly":False,"animal_popular":True,
    },
    "Koala": {
        "is_animal":True,"animal_mammal":True,"animal_australia":True,"animal_large":False,
        "animal_fur":True,"animal_fly":False,"animal_pet":False,"animal_popular":True, "animal_eggs": False,
    },
    "Platypus": {
        "is_animal":True,"animal_mammal":True,"animal_australia":True,"animal_water":True,
        "animal_eggs":True,"animal_swim":True,"animal_fly":False,"animal_popular":True,
    },
    "Polar Bear": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_fur":True,"animal_swim":True,"animal_predator":True,"animal_danger":True,
        "animal_fly":False,"animal_popular":True,
    },
    "Penguin": {
        "is_animal":True,"animal_bird":True,"animal_fly":False,"animal_swim":True,
        "animal_ocean":True,"animal_eggs":True,"animal_popular":True,
    },
    "Eagle": {
        "is_animal":True,"animal_bird":True,"animal_fly":True,"animal_large":False,
        "animal_predator":True,"animal_popular":True,
    },
    "Owl": {
        "is_animal":True,"animal_bird":True,"animal_fly":True,"animal_nocturnal":True,
        "animal_predator":True,"animal_4legs":False,
    },
    "Flamingo": {
        "is_animal":True,"animal_bird":True,"animal_fly":True,"animal_water":True,
        "animal_4legs":False,"animal_popular":True,
    },
    "Shark": {
        "is_animal":True,"animal_fish":True,"animal_ocean":True,"animal_water":True,
        "animal_swim":True,"animal_predator":True,"animal_danger":True,"animal_cold":True,
        "animal_large":True,"animal_popular":True,"animal_fly":False,
    },
    "Dolphin": {
        "is_animal":True,"animal_mammal":True,"animal_ocean":True,"animal_water":True,
        "animal_swim":True,"animal_fly":False,"animal_large":False,"animal_popular":True,
        "animal_danger":False,
    },
    "Whale": {
        "is_animal":True,"animal_mammal":True,"animal_ocean":True,"animal_water":True,
        "animal_swim":True,"animal_fly":False,"animal_large":True,"animal_popular":True,
    },
    "Octopus": {
        "is_animal":True,"animal_water":True,"animal_ocean":True,"animal_swim":True,
        "animal_4legs":False,"animal_cold":True,"animal_fly":False,"animal_venom":True,
        "animal_popular":True,
    },
    "Crab": {
        "is_animal":True,"animal_water":True,"animal_shell":True,"animal_small":True,
        "animal_cold":True,"animal_4legs":False,"animal_fly":False,
    },
    "Sea Turtle": {
        "is_animal":True,"animal_reptile":True,"animal_water":True,"animal_ocean":True,
        "animal_shell":True,"animal_swim":True,"animal_cold":True,"animal_eggs":True,
        "animal_fly":False,"animal_large":False,
    },
    "Frog": {
        "is_animal":True,"animal_water":True,"animal_4legs":True,"animal_cold":True,
        "animal_eggs":True,"animal_tiny":True,"animal_fly":False,"animal_venom":False,
    },
    "Snake": {
        "is_animal":True,"animal_reptile":True,"animal_cold":True,"animal_4legs":False,
        "animal_venom":True,"animal_eggs":True,"animal_fly":False,"animal_predator":True,
        "animal_danger":True,"animal_popular":True,
    },
    "Crocodile": {
        "is_animal":True,"animal_reptile":True,"animal_cold":True,"animal_4legs":True,
        "animal_water":True,"animal_danger":True,"animal_predator":True,"animal_eggs":True,
        "animal_large":True,"animal_fly":False,"animal_africa":True,
    },
    "Fox": {
        "is_animal":True,"animal_mammal":True,"animal_fur":True,"animal_4legs":True,
        "animal_predator":True,"animal_nocturnal":True,"animal_small":True,"animal_fly":False,
    },
    "Wolf": {
        "is_animal":True,"animal_mammal":True,"animal_fur":True,"animal_4legs":True,
        "animal_predator":True,"animal_large":False,"animal_fly":False,"animal_danger":True,
    },
    "Bear": {
        "is_animal":True,"animal_mammal":True,"animal_fur":True,"animal_4legs":True,
        "animal_large":True,"animal_predator":True,"animal_danger":True,"animal_fly":False,
        "animal_popular":True,
    },
    "Bee": {
        "is_animal":True,"animal_insect":True,"animal_fly":True,"animal_tiny":True,
        "animal_venom":True,"animal_popular":True,
    },
    "Butterfly": {
        "is_animal":True,"animal_insect":True,"animal_fly":True,"animal_tiny":True,
        "animal_popular":True,"animal_venom":False,
    },
    "Spider": {
        "is_animal":True,"animal_insect":True,"animal_tiny":True,"animal_fly":False,
        "animal_venom":True,"animal_nocturnal":True,"animal_predator":True,
    },
    "Bat": {
        "is_animal":True,"animal_mammal":True,"animal_fly":True,"animal_nocturnal":True,
        "animal_tiny":True,"animal_fur":True,
    },
    "Squirrel": {
        "is_animal":True,"animal_mammal":True,"animal_fur":True,"animal_4legs":True,
        "animal_tiny":True,"animal_fly":False,"animal_predator":False,
    },
    "Hedgehog": {
        "is_animal":True,"animal_mammal":True,"animal_tiny":True,"animal_4legs":True,
        "animal_nocturnal":True,"animal_fly":False,"animal_prickly":True,
    },
    "Deer": {
        "is_animal":True,"animal_mammal":True,"animal_large":False,"animal_4legs":True,
        "animal_fur":True,"animal_fly":False,"animal_horn":True,"animal_predator":False,
    },
    "Panda": {
        "is_animal":True,"animal_mammal":True,"animal_large":True,"animal_4legs":True,
        "animal_fur":True,"animal_fly":False,"animal_popular":True,"animal_predator":False,
    },

    # ── PLANTS ───────────────────────────────────────────────────────────────
    "Rose": {
        "is_plant":True,"plant_flower":True,"plant_colorful":True,"plant_fragrant":True,
        "plant_garden":True,"plant_prickly":True,"plant_edible":False,
    },
    "Sunflower": {
        "is_plant":True,"plant_flower":True,"plant_colorful":True,"plant_tall":True,
        "plant_garden":True,"plant_edible":True,"plant_fragrant":False,
    },
    "Tulip": {
        "is_plant":True,"plant_flower":True,"plant_colorful":True,"plant_garden":True,
        "plant_fragrant":False,"plant_prickly":False,
    },
    "Daisy": {
        "is_plant":True,"plant_flower":True,"plant_colorful":True,"plant_garden":True,
        "plant_fragrant":False,"plant_tall":False,
    },
    "Lavender": {
        "is_plant":True,"plant_flower":True,"plant_fragrant":True,"plant_colorful":True,
        "plant_garden":True,"plant_edible":False,
    },
    "Orchid": {
        "is_plant":True,"plant_flower":True,"plant_colorful":True,"plant_indoor":True,
        "plant_fragrant":False,"plant_garden":False,
    },
    "Oak Tree": {
        "is_plant":True,"plant_tree":True,"plant_tall":True,"plant_edible":False,
        "plant_needles":False,"plant_colorful":False,"plant_fruit":True,
    },
    "Pine Tree": {
        "is_plant":True,"plant_tree":True,"plant_tall":True,"plant_needles":True,
        "plant_edible":False,"plant_colorful":False,
    },
    "Apple Tree": {
        "is_plant":True,"plant_tree":True,"plant_tall":True,"plant_fruit":True,
        "plant_edible":True,"plant_needles":False,
    },
    "Cherry Tree": {
        "is_plant":True,"plant_tree":True,"plant_tall":True,"plant_fruit":True,
        "plant_colorful":True,"plant_edible":True,"plant_needles":False,
    },
    "Palm Tree": {
        "is_plant":True,"plant_tree":True,"plant_tall":True,"plant_fruit":True,
        "plant_desert":True,"plant_needles":False,"plant_colorful":False,
    },
    "Cactus": {
        "is_plant":True,"plant_desert":True,"plant_prickly":True,"plant_indoor":True,
        "plant_tree":False,"plant_flower":False,"plant_edible":False,
    },
    "Fern": {
        "is_plant":True,"plant_indoor":True,"plant_water":True,"plant_flower":False,
        "plant_tree":False,"plant_edible":False,"plant_prickly":False,
    },
    "Bamboo": {
        "is_plant":True,"plant_tall":True,"plant_edible":True,"plant_tree":False,
        "plant_flower":False,"plant_indoor":True,
    },
    "Grass": {
        "is_plant":True,"plant_edible":False,"plant_tall":False,"plant_garden":True,
        "plant_tree":False,"plant_flower":False,
    },
    "Ivy": {
        "is_plant":True,"plant_indoor":True,"plant_garden":True,"plant_tree":False,
        "plant_flower":False,"plant_edible":False,
    },
    "Water Lily": {
        "is_plant":True,"plant_flower":True,"plant_water":True,"plant_colorful":True,
        "plant_garden":True,"plant_edible":False,
    },
    "Seaweed": {
        "is_plant":True,"plant_water":True,"plant_edible":True,"plant_tree":False,
        "plant_flower":False,"plant_garden":False,
    },
    "Mushroom": {
        "is_fungus":True,"is_plant":False,"is_animal":False,"plant_edible":True,
        "plant_water":False,"plant_garden":True,
    },

    # ── FOOD & DRINK ─────────────────────────────────────────────────────────
    "Pizza": {
        "is_food":True,"food_italian":True,"food_baked":True,"food_meat":False,
        "food_fast":True,"food_hot":True,"food_sweet":False,"food_drink":False,
    },
    "Pasta": {
        "is_food":True,"food_italian":True,"food_baked":False,"food_hot":True,
        "food_sweet":False,"food_drink":False,"food_meat":False,
    },
    "Burger": {
        "is_food":True,"food_fast":True,"food_meat":True,"food_baked":False,
        "food_hot":True,"food_sweet":False,"food_drink":False,
    },
    "Sushi": {
        "is_food":True,"food_meat":True,"food_hot":False,"food_sweet":False,
        "food_fast":False,"food_drink":False,"food_baked":False,
    },
    "Soup": {
        "is_food":True,"food_hot":True,"food_sweet":False,"food_drink":False,
        "food_baked":False,"food_fast":False,
    },
    "Salad": {
        "is_food":True,"food_hot":False,"food_sweet":False,"food_veg":True,
        "food_meat":False,"food_baked":False,"food_drink":False,
    },
    "Sandwich": {
        "is_food":True,"food_baked":False,"food_hot":False,"food_sweet":False,
        "food_fast":True,"food_drink":False,
    },
    "Ice Cream": {
        "is_food":True,"food_sweet":True,"food_frozen":True,"food_dairy":True,
        "food_hot":False,"food_drink":False,"food_baked":False,
    },
    "Cake": {
        "is_food":True,"food_sweet":True,"food_baked":True,"food_dairy":True,
        "food_hot":False,"food_drink":False,
    },
    "Chocolate": {
        "is_food":True,"food_sweet":True,"food_snack":True,"food_baked":False,
        "food_hot":False,"food_drink":False,
    },
    "Chips / Crisps": {
        "is_food":True,"food_snack":True,"food_sweet":False,"food_baked":False,
        "food_hot":False,"food_drink":False,"food_fast":True,
    },
    "Bread": {
        "is_food":True,"food_baked":True,"food_sweet":False,"food_hot":False,
        "food_drink":False,"food_fast":False,
    },
    "Cheese": {
        "is_food":True,"food_dairy":True,"food_sweet":False,"food_hot":False,
        "food_drink":False,"food_baked":False,
    },
    "Egg": {
        "is_food":True,"food_breakfast":True,"food_sweet":False,"food_hot":True,
        "food_drink":False,"food_baked":False,"food_dairy":False,
    },
    "Apple": {
        "is_food":True,"food_fruit_item":True,"food_sweet":True,"food_hot":False,
        "food_drink":False,"food_snack":True,"food_veg":False,
    },
    "Banana": {
        "is_food":True,"food_fruit_item":True,"food_sweet":True,"food_hot":False,
        "food_drink":False,"food_snack":True,
    },
    "Orange": {
        "is_food":True,"food_fruit_item":True,"food_sweet":True,"food_hot":False,
        "food_drink":False,"food_snack":True,
    },
    "Strawberry": {
        "is_food":True,"food_fruit_item":True,"food_sweet":True,"food_hot":False,
        "food_drink":False,"food_snack":True,
    },
    "Carrot": {
        "is_food":True,"food_veg":True,"food_sweet":False,"food_hot":False,
        "food_drink":False,"food_snack":True,"food_fruit_item":False,
    },
    "Potato": {
        "is_food":True,"food_veg":True,"food_sweet":False,"food_hot":True,
        "food_drink":False,"food_baked":True,
    },
    "Coffee": {
        "is_food":True,"food_drink":True,"food_hot":True,"food_caffeine":True,
        "food_sweet":False,"food_alcohol":False,"food_fizzy":False,
    },
    "Tea": {
        "is_food":True,"food_drink":True,"food_hot":True,"food_caffeine":True,
        "food_sweet":False,"food_alcohol":False,"food_fizzy":False,
    },
    "Water": {
        "is_food":True,"food_drink":True,"food_hot":False,"food_caffeine":False,
        "food_sweet":False,"food_alcohol":False,"food_fizzy":False,
    },
    "Cola": {
        "is_food":True,"food_drink":True,"food_fizzy":True,"food_caffeine":True,
        "food_sweet":True,"food_alcohol":False,"food_hot":False,
    },
    "Orange Juice": {
        "is_food":True,"food_drink":True,"food_sweet":True,"food_hot":False,
        "food_alcohol":False,"food_fizzy":False,"food_caffeine":False,
    },
    "Lemonade": {
        "is_food":True, "food_drink":True,"food_sweet":True,"food_hot":False,
        "food_alcohol":False,"food_fizzy":False,"food_caffeine":False, "food_yellow":True,
    },
    "Beer": {
        "is_food":True,"food_drink":True,"food_alcohol":True,"food_fizzy":True,
        "food_hot":False,"food_sweet":False,
    },
    "Wine": {
        "is_food":True,"food_drink":True,"food_alcohol":True,"food_fizzy":False,
        "food_hot":False,"food_sweet":False,
    },
    "Milk": {
        "is_food":True,"food_drink":True,"food_dairy":True,"food_hot":False,
        "food_alcohol":False,"food_sweet":False,"food_fizzy":False,
    },
    "Hot Chocolate": {
        "is_food":True,"food_drink":True,"food_hot":True,"food_sweet":True,
        "food_alcohol":False,"food_caffeine":False,"food_fizzy":False,
    },

    # ── OBJECTS ───────────────────────────────────────────────────────────────
    "Smartphone": {
        "is_object":True,"obj_electronic":True,"obj_screen":True,"obj_portable":True,
        "obj_battery":True,"obj_modern":True,"obj_metal":False,
    },
    "Laptop": {
        "is_object":True,"obj_electronic":True,"obj_screen":True,"obj_portable":True,
        "obj_battery":True,"obj_modern":True,"obj_school":True,
    },
    "Television": {
        "is_object":True,"obj_electronic":True,"obj_screen":True,"obj_portable":False,
        "obj_battery":False,"obj_modern":True,"obj_bedroom":True,
    },
    "Tablet": {
        "is_object":True,"obj_electronic":True,"obj_screen":True,"obj_portable":True,
        "obj_battery":True,"obj_modern":True,
    },
    "Camera": {
        "is_object":True,"obj_electronic":True,"obj_portable":True,"obj_battery":True,
        "obj_screen":True,"obj_modern":True,
    },
    "Headphones": {
        "is_object":True,"obj_electronic":True,"obj_portable":True,"obj_battery":True,
        "obj_music":True,"obj_screen":False,"obj_modern":True,
    },
    "Clock": {
        "is_object":True,"obj_electronic":False,"obj_screen":False,"obj_portable":False,
        "obj_bedroom":True,"obj_modern":False,"obj_metal":True,
    },
    "Watch": {
        "is_object":True,"obj_electronic":True,"obj_portable":True,"obj_clothing":True,
        "obj_modern":True,"obj_metal":True,
    },
    "Chair": {
        "is_object":True,"obj_furniture":True,"obj_electronic":False,"obj_metal":False,
        "obj_portable":False,"obj_school":True,
    },
    "Table": {
        "is_object":True,"obj_furniture":True,"obj_electronic":False,"obj_portable":False,
        "obj_school":True,
    },
    "Bed": {
        "is_object":True,"obj_furniture":True,"obj_electronic":False,"obj_portable":False,
        "obj_bedroom":True,
    },
    "Sofa": {
        "is_object":True,"obj_furniture":True,"obj_electronic":False,"obj_portable":False,
        "obj_bedroom":False,
    },
    "Fridge": {
        "is_object":True,"obj_kitchen":True,"obj_electronic":True,"obj_portable":False,
        "obj_screen":False,"obj_battery":False,
    },
    "Microwave": {
        "is_object":True,"obj_kitchen":True,"obj_electronic":True,"obj_portable":False,
        "obj_screen":False,"obj_battery":False,
    },
    "Oven": {
        "is_object":True,"obj_kitchen":True,"obj_electronic":False,"obj_portable":False,
        "obj_metal":True,
    },
    "Kettle": {
        "is_object":True,"obj_kitchen":True,"obj_electronic":True,"obj_portable":True,
        "obj_battery":False,"obj_screen":False,
    },
    "Knife": {
        "is_object":True,"obj_kitchen":True,"obj_cutting":True,"obj_metal":True,
        "obj_electronic":False,"obj_portable":True,
    },
    "Pen": {
        "is_object":True,"obj_writing":True,"obj_portable":True,"obj_school":True,
        "obj_electronic":False,"obj_battery":False,"obj_tiny":True,
    },
    "Pencil": {
        "is_object":True,"obj_writing":True,"obj_portable":True,"obj_school":True,
        "obj_electronic":False,"obj_battery":False,"obj_tiny":True,
    },
    "Book": {
        "is_object":True,"obj_school":True,"obj_portable":True,"obj_electronic":False,
        "obj_battery":False,"obj_writing":False,
    },
    "Backpack": {
        "is_object":True,"obj_carry":True,"obj_school":True,"obj_portable":True,
        "obj_electronic":False,"obj_clothing":False,
    },
    "Umbrella": {
        "is_object":True,"obj_portable":True,"obj_electronic":False,"obj_metal":True,
        "obj_carry":False,"obj_school":False,
    },
    "Bicycle": {
        "is_object":True,"obj_transport":True,"obj_portable":False,"obj_electronic":False,
        "obj_metal":True,"obj_battery":False,"obj_sport":True,
    },
    "Car": {
        "is_object":True,"obj_transport":True,"obj_electronic":True,"obj_metal":True,
        "obj_portable":False,"obj_modern":True,
    },
    "Guitar": {
        "is_object":True,"obj_music":True,"obj_portable":True,"obj_electronic":False,
        "obj_battery":False,"obj_metal":False,
    },
    "Football": {
        "is_object":True,"obj_sport":True,"obj_portable":True,"obj_electronic":False,
        "obj_battery":False,"obj_metal":False,
    },

    # ── PLACES ────────────────────────────────────────────────────────────────
    "Eiffel Tower": {
        "is_place":True,"place_landmark":True,"place_europe":True,"place_tourist":True,
        "place_country":False,"place_city":False,"place_natural":False,"place_ancient":False,
    },
    "Big Ben": {
        "is_place":True,"place_landmark":True,"place_europe":True,"place_tourist":True,
        "place_country":False,"place_city":False,"place_natural":False,
    },
    "Colosseum": {
        "is_place":True,"place_landmark":True,"place_europe":True,"place_ancient":True,
        "place_tourist":True,"place_country":False,"place_city":False,"place_natural":False,
    },
    "Stonehenge": {
        "is_place":True,"place_landmark":True,"place_europe":True,"place_ancient":True,
        "place_tourist":True,"place_natural":False,
    },
    "Taj Mahal": {
        "is_place":True,"place_landmark":True,"place_asia":True,"place_ancient":True,
        "place_tourist":True,"place_hot":True,
    },
    "Great Wall of China": {
        "is_place":True,"place_landmark":True,"place_asia":True,"place_ancient":True,
        "place_tourist":True,"place_large":True,
    },
    "Statue of Liberty": {
        "is_place":True,"place_landmark":True,"place_americas":True,"place_tourist":True,
        "place_ancient":False,
    },
    "Pyramids of Giza": {
        "is_place":True,"place_landmark":True,"place_africa":True,"place_ancient":True,
        "place_tourist":True,"place_hot":True,
    },
    "Sydney Opera House": {
        "is_place":True,"place_landmark":True,"place_tourist":True,"place_ancient":False,
    },
    "Machu Picchu": {
        "is_place":True,"place_landmark":True,"place_americas":True,"place_ancient":True,
        "place_tourist":True,
    },
    "Mount Fuji": {
        "is_place":True,"place_natural":True,"place_asia":True,"place_tourist":True,
        "place_landmark":False,"place_large":True,
    },
    "Mount Everest": {
        "is_place":True,"place_natural":True,"place_asia":True,"place_large":True,
        "place_cold":True,"place_tourist":False,
    },
    "Amazon River": {
        "is_place":True,"place_natural":True,"place_americas":True,"place_large":True,
        "place_hot":True,"place_ocean_area":True,
    },
    "River Nile": {
        "is_place":True,"place_natural":True,"place_africa":True,"place_large":True,
        "place_hot":True,"place_ancient":True,
    },
    "Sahara Desert": {
        "is_place":True,"place_natural":True,"place_africa":True,"place_large":True,
        "place_hot":True,
    },
    "Pacific Ocean": {
        "is_place":True,"place_natural":True,"place_large":True,"place_ocean_area":True,
        "place_cold":False,"place_ancient":False,
    },
    "France": {
        "is_place":True,"place_country":True,"place_europe":True,"place_tourist":True,
        "place_large":False,"place_island":False,"place_ancient":True,
    },
    "United Kingdom": {
        "is_place":True,"place_country":True,"place_europe":True,"place_island":True,
        "place_tourist":True,"place_cold":True,
    },
    "Germany": {
        "is_place":True,"place_country":True,"place_europe":True,"place_large":False,
        "place_island":False,"place_cold":False,
    },
    "Italy": {
        "is_place":True,"place_country":True,"place_europe":True,"place_ancient":True,
        "place_tourist":True,"place_hot":True,
    },
    "Spain": {
        "is_place":True,"place_country":True,"place_europe":True,"place_tourist":True,
        "place_hot":True,"place_island":False,
    },
    "Russia": {
        "is_place":True,"place_country":True,"place_europe":True,"place_asia":True,
        "place_large":True,"place_cold":True,
    },
    "USA": {
        "is_place":True,"place_country":True,"place_americas":True,"place_large":True,
        "place_tourist":True,"place_ancient":False,
    },
    "Brazil": {
        "is_place":True,"place_country":True,"place_americas":True,"place_large":True,
        "place_hot":True,"place_tourist":True,
    },
    "Canada": {
        "is_place":True,"place_country":True,"place_americas":True,"place_large":True,
        "place_cold":True,
    },
    "China": {
        "is_place":True,"place_country":True,"place_asia":True,"place_large":True,
        "place_ancient":True,"place_tourist":True,
    },
    "India": {
        "is_place":True,"place_country":True,"place_asia":True,"place_large":True,
        "place_hot":True,"place_ancient":True,
    },
    "Japan": {
        "is_place":True,"place_country":True,"place_asia":True,"place_island":True,
        "place_tourist":True,"place_ancient":True,
    },
    "Australia": {
        "is_place":True,"place_country":True,"place_large":True,"place_island":True,
        "place_hot":True,"place_tourist":True,
    },
    "Egypt": {
        "is_place":True,"place_country":True,"place_africa":True,"place_ancient":True,
        "place_hot":True,"place_tourist":True,
    },
    "South Africa": {
        "is_place":True,"place_country":True,"place_africa":True,"place_large":False,
        "place_tourist":True,
    },
    "London": {
        "is_place":True,"place_city":True,"place_capital":True,"place_europe":True,
        "place_tourist":True,"place_cold":True,"place_ancient":True,
    },
    "Paris": {
        "is_place":True,"place_city":True,"place_capital":True,"place_europe":True,
        "place_tourist":True,
    },
    "New York": {
        "is_place":True,"place_city":True,"place_capital":False,"place_americas":True,
        "place_tourist":True,"place_large":True,
    },
    "Tokyo": {
        "is_place":True,"place_city":True,"place_capital":True,"place_asia":True,
        "place_tourist":True,"place_large":True,
    },
    "Dubai": {
        "is_place":True,"place_city":True,"place_capital":False,"place_asia":True,
        "place_hot":True,"place_tourist":True,"place_modern":True,
    },
    "Rome": {
        "is_place":True,"place_city":True,"place_capital":True,"place_europe":True,
        "place_ancient":True,"place_tourist":True,
    },

    # ── ELEMENTS ──────────────────────────────────────────────────────────────
    "Gold": {
        "is_element":True,"elem_metal":True,"elem_precious":True,"elem_conduct":True,
        "elem_jewellery":True,"elem_toxic":False,"elem_life":False,"elem_gas_rt":False,
        "elem_magnetic":False,
    },
    "Silver": {
        "is_element":True,"elem_metal":True,"elem_precious":True,"elem_conduct":True,
        "elem_jewellery":True,"elem_toxic":False,"elem_life":False,"elem_gas_rt":False,
        "elem_magnetic":False,
    },
    "Iron": {
        "is_element":True,"elem_metal":True,"elem_magnetic":True,"elem_conduct":True,
        "elem_precious":False,"elem_toxic":False,"elem_life":True,"elem_gas_rt":False,
        "elem_common":True,
    },
    "Copper": {
        "is_element":True,"elem_metal":True,"elem_conduct":True,"elem_precious":False,
        "elem_magnetic":False,"elem_toxic":False,"elem_gas_rt":False,"elem_common":True,
    },
    "Aluminium": {
        "is_element":True,"elem_metal":True,"elem_light":True,"elem_conduct":True,
        "elem_precious":False,"elem_magnetic":False,"elem_gas_rt":False,"elem_common":True,
    },
    "Mercury": {
        "is_element":True,"elem_metal":True,"elem_liquid_rt":True,"elem_toxic":True,
        "elem_precious":False,"elem_gas_rt":False,"elem_magnetic":False,
    },
    "Oxygen": {
        "is_element":True,"elem_gas_rt":True,"elem_life":True,"elem_breathe":True,
        "elem_metal":False,"elem_toxic":False,"elem_common":True,"elem_light":True,
    },
    "Hydrogen": {
        "is_element":True,"elem_gas_rt":True,"elem_life":True,"elem_light":True,
        "elem_breathe":False,"elem_metal":False,"elem_common":True,
    },
    "Nitrogen": {
        "is_element":True,"elem_gas_rt":True,"elem_breathe":True,"elem_life":True,
        "elem_metal":False,"elem_toxic":False,"elem_common":True,
    },
    "Carbon": {
        "is_element":True,"elem_metal":False,"elem_gas_rt":False,"elem_life":True,
        "elem_common":True,"elem_conduct":True,
    },
    "Helium": {
        "is_element":True,"elem_gas_rt":True,"elem_light":True,"elem_breathe":False,
        "elem_metal":False,"elem_toxic":False,"elem_life":False,
    },
    "Chlorine": {
        "is_element":True,"elem_gas_rt":True,"elem_toxic":True,"elem_life":False,
        "elem_metal":False,"elem_breathe":False,
    },
    "Platinum": {
        "is_element":True,"elem_metal":True,"elem_precious":True,"elem_jewellery":True,
        "elem_conduct":True,"elem_toxic":False,"elem_gas_rt":False,"elem_magnetic":False,
    },

    # ── REAL PEOPLE ───────────────────────────────────────────────────────────
    "Albert Einstein": {
        "is_person":True,"person_scientist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_20c":True,"person_alive":False,
    },
    "Isaac Newton": {
        "is_person":True,"person_scientist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,
    },
    "Marie Curie": {
        "is_person":True,"person_scientist":True,"person_historical":True,"person_male":False,
        "person_european":True,"person_famous":True,"person_alive":False,"person_20c":True,
    },
    "Charles Darwin": {
        "is_person":True,"person_scientist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,
    },
    "Leonardo da Vinci": {
        "is_person":True,"person_scientist":True,"person_artist":True,"person_historical":True,
        "person_male":True,"person_european":True,"person_famous":True,"person_alive":False,
    },
    "Napoleon Bonaparte": {
        "is_person":True,"person_leader":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,
    },
    "Winston Churchill": {
        "is_person":True,"person_leader":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,"person_20c":True,
    },
    "Abraham Lincoln": {
        "is_person":True,"person_leader":True,"person_historical":True,"person_male":True,
        "person_american":True,"person_famous":True,"person_alive":False,
    },
    "Cleopatra": {
        "is_person":True,"person_leader":True,"person_historical":True,"person_male":False,
        "person_famous":True,"person_alive":False,
    },
    "Nelson Mandela": {
        "is_person":True,"person_leader":True,"person_male":True,"person_famous":True,
        "person_alive":False,"person_20c":True,"person_historical":False,
    },
    "William Shakespeare": {
        "is_person":True,"person_artist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,
    },
    "Beethoven": {
        "is_person":True,"person_artist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,
    },
    "Elvis Presley": {
        "is_person":True,"person_artist":True,"person_male":True,"person_american":True,
        "person_famous":True,"person_alive":False,"person_20c":True,"person_historical":False,
    },
    "Michael Jackson": {
        "is_person":True,"person_artist":True,"person_male":True,"person_american":True,
        "person_famous":True,"person_alive":False,"person_20c":True,"person_historical":False,
    },
    "Vincent van Gogh": {
        "is_person":True,"person_artist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,
    },
    "Lionel Messi": {
        "is_person":True,"person_athlete":True,"person_male":True,"person_famous":True,
        "person_alive":True,"person_20c":False,"person_historical":False,
    },
    "Serena Williams": {
        "is_person":True,"person_athlete":True,"person_male":False,"person_american":True,
        "person_famous":True,"person_alive":True,"person_historical":False,
    },
    "Usain Bolt": {
        "is_person":True,"person_athlete":True,"person_male":True,"person_famous":True,
        "person_alive":True,"person_american":False,"person_historical":False,
    },
    "Alan Turing": {
        "is_person":True,"person_scientist":True,"person_historical":True,"person_male":True,
        "person_european":True,"person_famous":True,"person_alive":False,"person_20c":True,
    },
    "Ada Lovelace": {
        "is_person":True,"person_scientist":True,"person_historical":True,"person_male":False,
        "person_european":True,"person_famous":True,"person_alive":False,
    },

    # ── FICTIONAL CHARACTERS ──────────────────────────────────────────────────
    "Harry Potter": {
        "is_character":True,"char_book":True,"char_film":True,"char_hero":True,
        "char_magic":True,"char_human":True,"char_child":True,"char_famous_story":True,
        "char_animated":False,"char_superhero":False,"char_villain":False,
    },
    "Sherlock Holmes": {
        "is_character":True,"char_book":True,"char_film":True,"char_hero":True,
        "char_human":True,"char_magic":False,"char_famous_story":True,
        "char_animated":False,"char_superhero":False,"char_child":False,
    },
    "Dracula": {
        "is_character":True,"char_book":True,"char_film":True,"char_villain":True,
        "char_human":False,"char_magic":True,"char_famous_story":True,
        "char_animated":False,"char_superhero":False,
    },
    "Frankenstein's Monster": {
        "is_character":True,"char_book":True,"char_film":True,"char_villain":False,
        "char_human":False,"char_magic":False,"char_famous_story":True,
        "char_animated":False,"char_superhero":False,
    },
    "Superman": {
        "is_character":True,"char_film":True,"char_superhero":True,"char_hero":True,
        "char_human":True,"char_magic":False,"char_famous_story":True,
        "char_animated":False,"char_book":False,
    },
    "Batman": {
        "is_character":True,"char_film":True,"char_superhero":True,"char_hero":True,
        "char_human":True,"char_magic":False,"char_famous_story":True,
        "char_animated":False,"char_book":False,
    },
    "Spider-Man": {
        "is_character":True,"char_film":True,"char_superhero":True,"char_hero":True,
        "char_human":True,"char_magic":False,"char_famous_story":True,
        "char_animated":False,"char_child":True,
    },
    "Iron Man": {
        "is_character":True,"char_film":True,"char_superhero":True,"char_hero":True,
        "char_human":True,"char_magic":False,"char_famous_story":True,"char_animated":False,
    },
    "Hermione Granger": {
        "is_character":True,"char_book":True,"char_film":True,"char_hero":True,
        "char_magic":True,"char_human":True,"char_child":True,"char_famous_story":True,
        "char_animated":False,"char_superhero":False,"char_villain":False,
    },
    "Darth Vader": {
        "is_character":True,"char_film":True,"char_villain":True,"char_human":True,
        "char_magic":True,"char_famous_story":True,"char_animated":False,
        "char_superhero":False,
    },
    "Gandalf": {
        "is_character":True,"char_book":True,"char_film":True,"char_hero":True,
        "char_magic":True,"char_human":True,"char_child":False,"char_famous_story":True,
        "char_animated":False,
    },
    "Frodo Baggins": {
        "is_character":True,"char_book":True,"char_film":True,"char_hero":True,
        "char_magic":False,"char_human":False,"char_child":True,"char_famous_story":True,
        "char_animated":False,
    },
    "Homer Simpson": {
        "is_character":True,"char_film":True,"char_animated":True,"char_human":True,
        "char_hero":False,"char_magic":False,"char_famous_story":True,
        "char_superhero":False,"char_book":False,
    },
    "Mickey Mouse": {
        "is_character":True,"char_animated":True,"char_animal_char":True,"char_hero":True,
        "char_magic":False,"char_famous_story":True,"char_film":True,
        "char_superhero":False,"char_book":False,
    },
    "Simba": {
        "is_character":True,"char_animated":True,"char_animal_char":True,"char_film":True,
        "char_hero":True,"char_magic":False,"char_famous_story":True,
        "char_superhero":False,"char_book":False,
    },
    "Elsa": {
        "is_character":True,"char_animated":True,"char_film":True,"char_human":True,
        "char_magic":True,"char_hero":True,"char_famous_story":True,
        "char_superhero":False,"char_villain":False,
    },
    "Mario": {
        "is_character":True,"char_game":True,"char_hero":True,"char_human":True,
        "char_animated":True,"char_magic":False,"char_famous_story":True,
        "char_superhero":False,"char_book":False,
    },
    "Pikachu": {
        "is_character":True,"char_game":True,"char_animated":True,"char_animal_char":True,
        "char_hero":True,"char_magic":True,"char_famous_story":True,
        "char_superhero":False,"char_book":False,
    },
    "James Bond": {
        "is_character":True,"char_film":True,"char_book":True,"char_hero":True,
        "char_human":True,"char_magic":False,"char_famous_story":True,
        "char_animated":False,"char_superhero":False,
    },
    "Winnie the Pooh": {
        "is_character":True,"char_book":True,"char_animated":True,"char_animal_char":True,
        "char_hero":True,"char_magic":False,"char_famous_story":True,
        "char_child":True,"char_superhero":False,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SMART GAME ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class GameEngine:
    """Runs the guessing logic for the 20 Questions game.

    Fixed version:
    - Finds the category first.
    - Stays inside that category.
    - Does NOT stop early just because it runs out of perfect split questions.
    - Uses harmless filler questions when needed so the game reaches 20 questions.
    """

    MAX_QUESTIONS = 20

    CATEGORY_TRAITS = [
        "is_animal",
        "is_plant",
        "is_food",
        "is_object",
        "is_place",
        "is_element",
        "is_person",
        "is_character",
        "is_fungus",
    ]

    CATEGORY_PREFIXES = {
        "is_animal": "animal_",
        "is_plant": "plant_",
        "is_food": "food_",
        "is_object": "obj_",
        "is_place": "place_",
        "is_element": "elem_",
        "is_person": "person_",
        "is_character": "char_",
        "is_fungus": "plant_",
    }

    #I wanted to add enough catergories to make it interesting and not super simple

    # These questions are used only if the selected category runs out of
    # database traits before question 20. They keep the game playable and
    # prevent it from stopping at 10, 12, or 15 questions.
    FILLER_QUESTIONS = [
        ("filler_common", "Is it something most people would recognize?"),
        ("filler_real", "Is it something that exists in real life?"),
        ("filler_seen_often", "Would you see it often in everyday life?"),
        ("filler_large", "Is it larger than a backpack?"),
        ("filler_small", "Could it fit in your hand?"),
        ("filler_outside", "Is it usually found outside?"),
        ("filler_inside", "Is it usually found indoors?"),
        ("filler_natural", "Is it naturally occurring?"),
        ("filler_human_made", "Is it made or strongly shaped by humans?"),
        ("filler_colorful", "Is it known for having a noticeable color?"),
        ("filler_moving", "Can it move on its own?"),
        ("filler_useful", "Is it useful to people?"),
        ("filler_fun", "Is it connected to fun or entertainment?"),
        ("filler_old", "Has it existed for a very long time?"),
        ("filler_school", "Could it be talked about in school?"),
        ("filler_home", "Could it be found in or near a home?"),
        ("filler_expensive", "Is it usually expensive?"),
        ("filler_safe", "Is it usually safe to be around?"),
        ("filler_famous", "Is it famous or well known?"),
        ("filler_specific", "Are you thinking of a specific one rather than a general type?"),
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self.candidates = list(ANSWERS.keys())
        self.asked = {}
        self.question_num = 0
        self.category = None
        self.category_not_found = False

    def _score_question(self, trait):
        yes_count = sum(1 for item in self.candidates if ANSWERS[item].get(trait) is True)
        no_count = sum(1 for item in self.candidates if ANSWERS[item].get(trait) is False)

        total = yes_count + no_count
        if total == 0:
            return -1

        # Bigger is better. A perfect split has a score close to 0.
        return -abs(yes_count - no_count)

    def _next_category_question(self):
        for trait in self.CATEGORY_TRAITS:
            if trait not in self.asked:
                return trait, QUESTIONS[trait]
        return None, None

    def _next_category_specific_question(self):
        prefix = self.CATEGORY_PREFIXES.get(self.category)
        if not prefix:
            return None, None

        possible_traits = set()
        for item in self.candidates:
            for trait in ANSWERS[item]:
                if trait.startswith(prefix) and trait not in self.asked:
                    possible_traits.add(trait)

        if not possible_traits:
            return None, None

        # Prefer questions that split the remaining candidates.
        scored_traits = [(self._score_question(trait), trait) for trait in possible_traits]
        scored_traits = [(score, trait) for score, trait in scored_traits if score != -1]

        if scored_traits:
            scored_traits.sort(reverse=True)
            best_trait = scored_traits[0][1]
            return best_trait, QUESTIONS.get(best_trait, f"Is it related to {best_trait}?")

        # If no question splits perfectly, still ask an unused category question.
        best_trait = sorted(possible_traits)[0]
        return best_trait, QUESTIONS.get(best_trait, f"Is it related to {best_trait}?")

    def _next_filler_question(self):
        for trait, question in self.FILLER_QUESTIONS:
            if trait not in self.asked:
                return trait, question
        return None, None

    def next_question(self):
        if self.question_num >= self.MAX_QUESTIONS:
            return None, None

        # Phase 1: identify the category first.
        if self.category is None:
            return self._next_category_question()

        # Phase 2: ask questions from the selected category.
        trait, question = self._next_category_specific_question()
        if trait is not None:
            return trait, question

        # Phase 3: if the category has no unused traits left, ask safe filler
        # questions until question 20 instead of jumping to a guess early.
        return self._next_filler_question()

    def answer(self, trait, response: bool):
        self.asked[trait] = response
        self.question_num += 1

        # Category questions decide which category to lock into.
        if trait in self.CATEGORY_TRAITS:
            if response:
                self.category = trait
                matching = [
                    item for item in self.candidates
                    if ANSWERS[item].get(trait) is True
                ]
                if matching:
                    self.candidates = matching
            else:
                self.candidates = [
                    item for item in self.candidates
                    if ANSWERS[item].get(trait) is not True
                ]

                if all(category in self.asked for category in self.CATEGORY_TRAITS):
                    self.category_not_found = True
            return

        # Filler questions are only for pacing. They should NOT eliminate answers,
        # because they are not part of the database.
        if trait.startswith("filler_"):
            return

        # Normal category-specific filtering.
        filtered = []
        for item in self.candidates:
            value = ANSWERS[item].get(trait)

            # Unknown traits stay possible instead of instantly removing the answer.
            if value is None or value == response:
                filtered.append(item)

        # Never wipe out the whole candidate list from one answer.
        if filtered:
            self.candidates = filtered

    def should_guess(self):
        # The game should only guess at 20 questions, or if the category cannot be found.
        if self.question_num >= self.MAX_QUESTIONS:
            return True

        if self.category_not_found:
            return True

        # If there are literally no database or filler questions left, then guess.
        trait, _ = self.next_question()
        return trait is None

    def best_guess(self):
        if self.category_not_found:
            return "I could not find that category in my database."

        if not self.candidates:
            return "I could not narrow it down, but try again with a common answer from the database."

        # Pick the candidate that matches the most answered database traits.
        def match_score(item):
            score = 0
            for trait, response in self.asked.items():
                if trait.startswith("filler_"):
                    continue
                if ANSWERS[item].get(trait) == response:
                    score += 1
            return score

        return max(self.candidates, key=match_score)


# ══════════════════════════════════════════════════════════════════════════════
#  PARTICLES
# ══════════════════════════════════════════════════════════════════════════════
class Particle:
    SYMBOLS = ["✦","★","✸","·","✺","◆"]
    def __init__(self, canvas):
        self.canvas = canvas
        self.x  = random.randint(100,620)
        self.y  = random.randint(150,430)
        self.vx = random.uniform(-1.5,1.5)
        self.vy = random.uniform(-3.5,-1.0)
        self.alpha = 1.0
        color = random.choice(["#b48aff","#7c5cff","#e0d4ff","#ffffff","#ffdd88"])
        self.id = canvas.create_text(self.x, self.y,
            text=random.choice(self.SYMBOLS),
            font=("Arial", random.randint(12,20)), fill=color)
    def step(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.08
        self.alpha -= 0.025
        if self.alpha > 0.05:
            self.canvas.coords(self.id, self.x, self.y)
            return True
        return False
    def remove(self):
        try: self.canvas.delete(self.id)
        except: pass


# ══════════════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════════════
class TwentyQuestions:
    BG      = "#0d0d1a"
    CARD    = "#16162a"
    ACCENT  = "#7c5cff"
    ACCENT2 = "#b48aff"
    YES_COL = "#22c55e"
    NO_COL  = "#ef4444"
    TEXT    = "#e8e8ff"
    MUTED   = "#888ab8"
    BORDER  = "#2e2e55"

    def __init__(self, root):
        self.root = root
        self.root.title("20 Questions")
        self.root.geometry("720x580")
        self.root.resizable(False, False)
        self.root.config(bg=self.BG)

        self.sound      = SoundEngine()
        self.engine     = GameEngine()
        self._particles = []
        self._cur_trait = None
        self.guessing   = False
        self.wins       = 0
        self.losses     = 0

        self._build_ui()
        self._draw_stars()
        self._animate()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.star_canvas = tk.Canvas(self.root, bg=self.BG,
            highlightthickness=0, width=720, height=580)
        self.star_canvas.place(x=0,y=0)

        tk.Label(self.root, text="20 Questions",
            font=("Georgia",26,"bold italic"), fg=self.ACCENT2, bg=self.BG).pack(pady=(22,2))
        tk.Label(self.root, text="Think of anything — I'll figure it out",
            font=("Georgia",11,"italic"), fg=self.MUTED, bg=self.BG).pack()

        sf = tk.Frame(self.root, bg=self.BG); sf.pack(pady=12)
        self.wins_var   = tk.StringVar(value="Computer: 0")
        self.losses_var = tk.StringVar(value="You: 0")
        for var,col in [(self.wins_var,self.YES_COL),(self.losses_var,self.NO_COL)]:
            f = tk.Frame(sf,bg=self.CARD,highlightthickness=1,highlightbackground=self.BORDER)
            f.pack(side="left",padx=10,ipady=6,ipadx=14)
            tk.Label(f,text="●",fg=col,bg=self.CARD,font=("Arial",10)).pack(side="left",padx=(0,6))
            tk.Label(f,textvariable=var,fg=col,bg=self.CARD,font=("Arial",11,"bold")).pack(side="left")

        pf = tk.Frame(self.root,bg=self.BG); pf.pack(fill="x",padx=48,pady=(4,0))
        self.prog_canvas = tk.Canvas(pf,height=8,bg="#1e1e38",
            highlightthickness=1,highlightbackground=self.BORDER)
        self.prog_canvas.pack(fill="x")
        self.prog_bar = self.prog_canvas.create_rectangle(0,0,0,8,fill=self.ACCENT,outline="")
        self.prog_label = tk.Label(self.root,text="",font=("Arial",10),fg=self.MUTED,bg=self.BG)
        self.prog_label.pack(pady=(3,6))

        self.card_frame = tk.Frame(self.root,bg=self.CARD,bd=0,
            highlightthickness=2,highlightbackground=self.BORDER)
        self.card_frame.pack(fill="x",padx=48,pady=4)
        self.question_label = tk.Label(self.card_frame,
            text="Click  Start  when you've thought of something!",
            font=("Georgia",15),fg=self.TEXT,bg=self.CARD,
            wraplength=580,padx=28,pady=32,justify="center")
        self.question_label.pack(fill="both")

        bf = tk.Frame(self.root,bg=self.BG); bf.pack(pady=14)
        self.start_btn = self._btn(bf,"Start",  self.ACCENT,  self.start_game, 13); self.start_btn.grid(row=0,column=0,padx=10)
        self.yes_btn   = self._btn(bf,"Yes",    self.YES_COL, lambda:self.answer(True),  11); self.yes_btn.grid(row=0,column=1,padx=10); self.yes_btn.config(state="disabled")
        self.no_btn    = self._btn(bf,"No",     self.NO_COL,  lambda:self.answer(False), 11); self.no_btn.grid(row=0,column=2,padx=10);  self.no_btn.config(state="disabled")

        bot = tk.Frame(self.root,bg=self.BG); bot.pack(pady=4)
        self._btn(bot,"Reset",self.BORDER,self.reset_game,12,10).pack(side="left",padx=10)
        self.sound_btn = self._btn(bot,
            "Sound: ON" if SOUND_AVAILABLE else "No pygame",
            self.BORDER, self._toggle_sound, 14, 10)
        self.sound_btn.pack(side="left",padx=10)
        if not SOUND_AVAILABLE:
            self.sound_btn.config(state="disabled",text="pip install pygame numpy")

    def _btn(self,parent,text,color,cmd,width=11,fsz=12):
        b = tk.Button(parent,text=text,font=("Arial",fsz,"bold"),
            bg=color,fg="white",activebackground=color,activeforeground="white",
            relief="flat",bd=0,width=width,pady=9,cursor="hand2",command=cmd)
        b.bind("<Enter>",lambda e:b.config(bg=self._light(color)))
        b.bind("<Leave>",lambda e:b.config(bg=color))
        return b

    @staticmethod
    def _light(h,a=30):
        h=h.lstrip("#"); r,g,b=(int(h[i:i+2],16) for i in(0,2,4))
        return f"#{min(255,r+a):02x}{min(255,g+a):02x}{min(255,b+a):02x}"

    def _draw_stars(self):
        for _ in range(55):
            x,y=random.randint(0,720),random.randint(0,580)
            r=random.choice([1,1,1,2])
            col=random.choice(["#b48aff","#7c5cff","#ffffff","#e0d4ff"])
            self.star_canvas.create_oval(x-r,y-r,x+r,y+r,fill=col,outline="")

    def _animate(self):
        alive=[]
        for p in self._particles:
            if p.step(): alive.append(p)
            else: p.remove()
        self._particles=alive
        self.root.after(30,self._animate)

    def _spawn_particles(self):
        for _ in range(18): self._particles.append(Particle(self.star_canvas))

    def _update_progress(self):
        self.prog_canvas.update_idletasks()
        w=self.prog_canvas.winfo_width()
        pct=self.engine.question_num/20
        self.prog_canvas.coords(self.prog_bar,0,0,int(w*pct),8)
        self.prog_label.config(
            text=f"Question {self.engine.question_num} of 20  —  {len(self.engine.candidates)} possible answers remaining")

    def _flash(self,color,steps=6):
        cols=[color,self.BORDER]*(steps//2)
        def _s(i=0):
            if i<len(cols):
                self.card_frame.config(highlightbackground=cols[i])
                self.root.after(80,lambda:_s(i+1))
            else: self.card_frame.config(highlightbackground=self.BORDER)
        _s()

    def _shake(self):
        offs=[6,-6,5,-5,3,-3,0]
        def _s(i=0):
            if i<len(offs):
                self.card_frame.pack_forget()
                self.card_frame.pack(fill="x",padx=(48+offs[i],48-offs[i]),pady=4)
                self.root.after(45,lambda:_s(i+1))
            else:
                self.card_frame.pack_forget()
                self.card_frame.pack(fill="x",padx=48,pady=4)
        self.card_frame.pack_forget(); _s()

    @staticmethod
    def _lerp(c1,c2,steps):
        def p(c):
            c=c.lstrip("#"); return tuple(int(c[i:i+2],16) for i in(0,2,4))
        r1,g1,b1=p(c1); r2,g2,b2=p(c2)
        return [f"#{int(r1+(r2-r1)*i/max(steps-1,1)):02x}"
                f"{int(g1+(g2-g1)*i/max(steps-1,1)):02x}"
                f"{int(b1+(b2-b1)*i/max(steps-1,1)):02x}" for i in range(steps)]

    def _fade(self,text,color=None,font=None):
        target_col = color or self.TEXT
        target_fnt = font  or ("Georgia",15)
        fade_out = self._lerp(self.TEXT, self.CARD, 6)
        fade_in  = self._lerp(self.CARD, target_col, 6)
        def do_out(i=0):
            if i<6:
                self.question_label.config(fg=fade_out[i])
                self.root.after(22,lambda:do_out(i+1))
            else:
                self.question_label.config(text=text,font=target_fnt,fg=self.CARD)
                do_in(0)
        def do_in(i=0):
            if i<6:
                self.question_label.config(fg=fade_in[i])
                self.root.after(22,lambda:do_in(i+1))
        do_out()

    # ── Game logic ────────────────────────────────────────────────────────────
    #How it runs
    def start_game(self):
        self.sound.play_start()
        self.engine.reset()
        self.guessing = False
        self.start_btn.config(state="disabled")
        self.yes_btn.config(text="Yes",state="normal")
        self.no_btn.config(text="No", state="normal")
        self.card_frame.config(highlightbackground=self.BORDER)
        self._ask_next()

    def _ask_next(self):
        trait, question = self.engine.next_question()

        if not trait or not question:
            self._do_guess()
            return

        self._cur_trait = trait
        self._fade(question)
        self._update_progress()
        self.sound.play_question()

    def answer(self, resp: bool):
        self.sound.play_click()
        if self.guessing:
            if resp:
                self.wins += 1
                self.wins_var.set(f"Computer: {self.wins}")
                self._flash(self.YES_COL,8)
                self.sound.play_win()
                self._spawn_particles()
            else:
                self.losses += 1
                self.losses_var.set(f"You: {self.losses}")
                self._flash(self.NO_COL,8)
                self._shake()
                self.sound.play_lose()
            self.yes_btn.config(state="disabled")
            self.no_btn.config(state="disabled")
            self.root.after(2200, self.reset_game)
            return

        if resp: self.sound.play_yes()
        else:    self.sound.play_no()

        self.engine.answer(self._cur_trait, resp)
        self._ask_next()

    def _do_guess(self):
        self.guessing = True
        guess = self.engine.best_guess()
        self.sound.play_guess()
        self._fade(f"My guess is:\n\n{guess}\n\nWas I right?",
                   color=self.ACCENT2, font=("Georgia",14,"bold italic"))
        self.prog_canvas.coords(self.prog_bar,0,0,self.prog_canvas.winfo_width(),8)
        self.prog_label.config(text="Final Guess!", fg=self.ACCENT2)
        self.yes_btn.config(text="Yes!")
        self.no_btn.config(text="Nope")

    def reset_game(self):
        self.engine.reset()
        self.guessing    = False
        self._cur_trait  = None
        self._fade("Click  Start  when you've thought of something!")
        self.prog_canvas.coords(self.prog_bar,0,0,0,8)
        self.prog_label.config(text="",fg=self.MUTED)
        self.card_frame.config(highlightbackground=self.BORDER)
        self.start_btn.config(state="normal")
        self.yes_btn.config(text="Yes",state="disabled")
        self.no_btn.config(text="No", state="disabled")

    def _toggle_sound(self):
        on = self.sound.toggle()
        self.sound_btn.config(text="Sound: ON" if on else "Sound: OFF")
        if on: self.sound.play_click()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    TwentyQuestions(root)
    root.mainloop()
    #this keeps it going in a loop instead of stopping short on questions.
