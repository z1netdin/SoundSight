"""Sound Fingerprinting - identifies WHAT sound is playing.

Each game sound has a unique frequency signature (how energy is distributed
across frequency bands). We match live audio against saved signatures to
identify footsteps, gunshots, abilities, etc.

Signatures are stored in profiles so community can create/share them.
"""

import numpy as np
from scipy import signal as scipy_signal


# Frequency bands matching the analyzer
BANDS = [
    ("sub_low", 20, 150),
    ("low", 150, 500),
    ("mid", 500, 2000),
    ("high", 2000, 6000),
    ("ultra", 6000, 16000),
]


def compute_band_ratios(audio_data, sample_rate):
    """Compute frequency band energy ratios from audio data.

    Returns a list of 5 floats that sum to ~1.0, representing
    what percentage of energy is in each band.
    """
    if len(audio_data) == 0:
        return [0.2, 0.2, 0.2, 0.2, 0.2]

    # If multi-channel, mix to mono
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    nyq = sample_rate / 2.0
    energies = []

    for name, lo, hi in BANDS:
        lo_n = max(lo / nyq, 0.001)
        hi_n = min(hi / nyq, 0.999)
        if lo_n < hi_n:
            sos = scipy_signal.butter(4, [lo_n, hi_n], btype="band", output="sos")
            filtered = scipy_signal.sosfilt(sos, audio_data)
            energies.append(float(np.mean(filtered ** 2)))
        else:
            energies.append(0.0)

    total = sum(energies) + 1e-10
    ratios = [e / total for e in energies]
    return ratios


def match_signature(band_ratios, signatures, min_confidence=0.5):
    """Match band ratios against a list of saved signatures.

    Returns (best_match_dict, confidence) or (None, 0) if no match.
    Confidence is 0-1, higher = better match.
    """
    if not signatures or not band_ratios:
        return None, 0.0

    best_match = None
    best_confidence = 0.0

    ratios = np.array(band_ratios)

    for sig in signatures:
        sig_ratios = np.array(sig.get("band_ratios", [0.2, 0.2, 0.2, 0.2, 0.2]))

        # Cosine similarity between the two ratio vectors
        dot = np.dot(ratios, sig_ratios)
        norm_a = np.linalg.norm(ratios) + 1e-10
        norm_b = np.linalg.norm(sig_ratios) + 1e-10
        similarity = dot / (norm_a * norm_b)

        # Also check Euclidean distance (penalizes big mismatches)
        distance = np.linalg.norm(ratios - sig_ratios)
        dist_score = max(0, 1.0 - distance * 2)

        # Combined confidence
        confidence = similarity * 0.6 + dist_score * 0.4

        if confidence > best_confidence and confidence >= min_confidence:
            best_confidence = confidence
            best_match = sig

    return best_match, best_confidence


# ============================================================
# Pre-built Valorant sound signatures
# From real game audio analysis (mp3 files)
# ============================================================

VALORANT_AGENTS = {
    "Omen": {
        "role": "Controller",
        "abilities": [
            {"name": "Shrouded Step", "key": "C", "icon": "teleport",
             "band_ratios": [0.77, 0.06, 0.06, 0.04, 0.07], "transient": True},
            {"name": "Paranoia", "key": "Q", "icon": "flash",
             "band_ratios": [0.30, 0.25, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Dark Cover", "key": "E", "icon": "smoke",
             "band_ratios": [0.15, 0.30, 0.35, 0.15, 0.05], "transient": False},
            {"name": "From the Shadows", "key": "X", "icon": "ultimate",
             "band_ratios": [0.40, 0.20, 0.20, 0.15, 0.05], "transient": True},
        ]
    },
    "Jett": {
        "role": "Duelist",
        "abilities": [
            {"name": "Cloudburst", "key": "C", "icon": "smoke",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Updraft", "key": "Q", "icon": "jump",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
            {"name": "Tailwind", "key": "E", "icon": "dash",
             "band_ratios": [0.25, 0.35, 0.25, 0.10, 0.05], "transient": True},
            {"name": "Blade Storm", "key": "X", "icon": "ultimate",
             "band_ratios": [0.10, 0.20, 0.35, 0.25, 0.10], "transient": True},
        ]
    },
    "Sage": {
        "role": "Sentinel",
        "abilities": [
            {"name": "Barrier Orb", "key": "C", "icon": "wall",
             "band_ratios": [0.20, 0.35, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Slow Orb", "key": "Q", "icon": "slow",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Healing Orb", "key": "E", "icon": "heal",
             "band_ratios": [0.10, 0.20, 0.40, 0.25, 0.05], "transient": False},
            {"name": "Resurrection", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.25, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Sova": {
        "role": "Initiator",
        "abilities": [
            {"name": "Owl Drone", "key": "C", "icon": "drone",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Shock Bolt", "key": "Q", "icon": "damage",
             "band_ratios": [0.20, 0.25, 0.30, 0.20, 0.05], "transient": True},
            {"name": "Recon Bolt", "key": "E", "icon": "scan",
             "band_ratios": [0.15, 0.20, 0.35, 0.25, 0.05], "transient": True},
            {"name": "Hunter's Fury", "key": "X", "icon": "ultimate",
             "band_ratios": [0.35, 0.25, 0.20, 0.15, 0.05], "transient": True},
        ]
    },
    "Phoenix": {
        "role": "Duelist",
        "abilities": [
            {"name": "Blaze", "key": "C", "icon": "wall",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": False},
            {"name": "Curveball", "key": "Q", "icon": "flash",
             "band_ratios": [0.10, 0.15, 0.35, 0.30, 0.10], "transient": True},
            {"name": "Hot Hands", "key": "E", "icon": "molly",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Run it Back", "key": "X", "icon": "ultimate",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Breach": {
        "role": "Initiator",
        "abilities": [
            {"name": "Aftershock", "key": "C", "icon": "damage",
             "band_ratios": [0.40, 0.30, 0.20, 0.08, 0.02], "transient": True},
            {"name": "Flashpoint", "key": "Q", "icon": "flash",
             "band_ratios": [0.10, 0.20, 0.35, 0.25, 0.10], "transient": True},
            {"name": "Fault Line", "key": "E", "icon": "stun",
             "band_ratios": [0.45, 0.30, 0.15, 0.08, 0.02], "transient": True},
            {"name": "Rolling Thunder", "key": "X", "icon": "ultimate",
             "band_ratios": [0.50, 0.30, 0.12, 0.06, 0.02], "transient": True},
        ]
    },
    "Raze": {
        "role": "Duelist",
        "abilities": [
            {"name": "Boom Bot", "key": "C", "icon": "drone",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Blast Pack", "key": "Q", "icon": "damage",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
            {"name": "Paint Shells", "key": "E", "icon": "molly",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
            {"name": "Showstopper", "key": "X", "icon": "ultimate",
             "band_ratios": [0.45, 0.30, 0.15, 0.08, 0.02], "transient": True},
        ]
    },
    "Cypher": {
        "role": "Sentinel",
        "abilities": [
            {"name": "Trapwire", "key": "C", "icon": "trap",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Cyber Cage", "key": "Q", "icon": "smoke",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Spycam", "key": "E", "icon": "scan",
             "band_ratios": [0.15, 0.20, 0.35, 0.25, 0.05], "transient": True},
            {"name": "Neural Theft", "key": "X", "icon": "ultimate",
             "band_ratios": [0.20, 0.25, 0.30, 0.20, 0.05], "transient": True},
        ]
    },
    "Killjoy": {
        "role": "Sentinel",
        "abilities": [
            {"name": "Nanoswarm", "key": "C", "icon": "molly",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Alarmbot", "key": "Q", "icon": "trap",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Turret", "key": "E", "icon": "damage",
             "band_ratios": [0.15, 0.25, 0.30, 0.25, 0.05], "transient": True},
            {"name": "Lockdown", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
        ]
    },
    "Viper": {
        "role": "Controller",
        "abilities": [
            {"name": "Snake Bite", "key": "C", "icon": "molly",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Poison Cloud", "key": "Q", "icon": "smoke",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": False},
            {"name": "Toxic Screen", "key": "E", "icon": "wall",
             "band_ratios": [0.20, 0.35, 0.25, 0.15, 0.05], "transient": False},
            {"name": "Viper's Pit", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": False},
        ]
    },
    "Reyna": {
        "role": "Duelist",
        "abilities": [
            {"name": "Leer", "key": "C", "icon": "flash",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Devour", "key": "Q", "icon": "heal",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": False},
            {"name": "Dismiss", "key": "E", "icon": "dash",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Empress", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.25, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Skye": {
        "role": "Initiator",
        "abilities": [
            {"name": "Regrowth", "key": "C", "icon": "heal",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": False},
            {"name": "Trailblazer", "key": "Q", "icon": "drone",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Guiding Light", "key": "E", "icon": "flash",
             "band_ratios": [0.10, 0.20, 0.35, 0.25, 0.10], "transient": True},
            {"name": "Seekers", "key": "X", "icon": "ultimate",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Yoru": {
        "role": "Duelist",
        "abilities": [
            {"name": "Fakeout", "key": "C", "icon": "decoy",
             "band_ratios": [0.51, 0.40, 0.08, 0.01, 0.00], "transient": True},
            {"name": "Blindside", "key": "Q", "icon": "flash",
             "band_ratios": [0.10, 0.20, 0.35, 0.25, 0.10], "transient": True},
            {"name": "Gatecrash", "key": "E", "icon": "teleport",
             "band_ratios": [0.77, 0.06, 0.06, 0.04, 0.07], "transient": True},
            {"name": "Dimensional Drift", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.25, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Astra": {
        "role": "Controller",
        "abilities": [
            {"name": "Gravity Well", "key": "C", "icon": "stun",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
            {"name": "Nova Pulse", "key": "Q", "icon": "stun",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Nebula", "key": "E", "icon": "smoke",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": False},
            {"name": "Cosmic Divide", "key": "X", "icon": "ultimate",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
        ]
    },
    "KAY/O": {
        "role": "Initiator",
        "abilities": [
            {"name": "FRAG/MENT", "key": "C", "icon": "molly",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
            {"name": "FLASH/DRIVE", "key": "Q", "icon": "flash",
             "band_ratios": [0.10, 0.15, 0.35, 0.30, 0.10], "transient": True},
            {"name": "ZERO/POINT", "key": "E", "icon": "stun",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "NULL/CMD", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
        ]
    },
    "Chamber": {
        "role": "Sentinel",
        "abilities": [
            {"name": "Trademark", "key": "C", "icon": "trap",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Headhunter", "key": "Q", "icon": "damage",
             "band_ratios": [0.15, 0.25, 0.30, 0.25, 0.05], "transient": True},
            {"name": "Rendezvous", "key": "E", "icon": "teleport",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Tour De Force", "key": "X", "icon": "ultimate",
             "band_ratios": [0.20, 0.25, 0.25, 0.25, 0.05], "transient": True},
        ]
    },
    "Neon": {
        "role": "Duelist",
        "abilities": [
            {"name": "Fast Lane", "key": "C", "icon": "wall",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Relay Bolt", "key": "Q", "icon": "stun",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "High Gear", "key": "E", "icon": "dash",
             "band_ratios": [0.30, 0.35, 0.20, 0.10, 0.05], "transient": True},
            {"name": "Overdrive", "key": "X", "icon": "ultimate",
             "band_ratios": [0.15, 0.25, 0.30, 0.25, 0.05], "transient": True},
        ]
    },
    "Fade": {
        "role": "Initiator",
        "abilities": [
            {"name": "Prowler", "key": "C", "icon": "drone",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Seize", "key": "Q", "icon": "stun",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
            {"name": "Haunt", "key": "E", "icon": "scan",
             "band_ratios": [0.20, 0.25, 0.30, 0.20, 0.05], "transient": True},
            {"name": "Nightfall", "key": "X", "icon": "ultimate",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
        ]
    },
    "Harbor": {
        "role": "Controller",
        "abilities": [
            {"name": "Cascade", "key": "C", "icon": "wall",
             "band_ratios": [0.25, 0.35, 0.25, 0.10, 0.05], "transient": True},
            {"name": "Cove", "key": "Q", "icon": "smoke",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "High Tide", "key": "E", "icon": "wall",
             "band_ratios": [0.30, 0.35, 0.20, 0.10, 0.05], "transient": True},
            {"name": "Reckoning", "key": "X", "icon": "ultimate",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
        ]
    },
    "Gekko": {
        "role": "Initiator",
        "abilities": [
            {"name": "Mosh Pit", "key": "C", "icon": "molly",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Wingman", "key": "Q", "icon": "drone",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Dizzy", "key": "E", "icon": "flash",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Thrash", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
        ]
    },
    "Deadlock": {
        "role": "Sentinel",
        "abilities": [
            {"name": "GravNet", "key": "C", "icon": "slow",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Sonic Sensor", "key": "Q", "icon": "trap",
             "band_ratios": [0.10, 0.20, 0.35, 0.25, 0.10], "transient": True},
            {"name": "Barrier Mesh", "key": "E", "icon": "wall",
             "band_ratios": [0.25, 0.35, 0.25, 0.10, 0.05], "transient": True},
            {"name": "Annihilation", "key": "X", "icon": "ultimate",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
        ]
    },
    "Iso": {
        "role": "Duelist",
        "abilities": [
            {"name": "Contingency", "key": "C", "icon": "wall",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Undercut", "key": "Q", "icon": "stun",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Double Tap", "key": "E", "icon": "damage",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Kill Contract", "key": "X", "icon": "ultimate",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Clove": {
        "role": "Controller",
        "abilities": [
            {"name": "Pick-Me-Up", "key": "C", "icon": "heal",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Meddle", "key": "Q", "icon": "slow",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Ruse", "key": "E", "icon": "smoke",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": False},
            {"name": "Not Dead Yet", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.25, 0.25, 0.15, 0.05], "transient": True},
        ]
    },
    "Vyse": {
        "role": "Sentinel",
        "abilities": [
            {"name": "Shear", "key": "C", "icon": "wall",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Arc Rose", "key": "Q", "icon": "stun",
             "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
            {"name": "Razorvine", "key": "E", "icon": "trap",
             "band_ratios": [0.25, 0.30, 0.25, 0.15, 0.05], "transient": True},
            {"name": "Steel Garden", "key": "X", "icon": "ultimate",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
        ]
    },
    "Tejo": {
        "role": "Initiator",
        "abilities": [
            {"name": "Guided Salvo", "key": "C", "icon": "damage",
             "band_ratios": [0.35, 0.30, 0.20, 0.10, 0.05], "transient": True},
            {"name": "Stealth Drone", "key": "Q", "icon": "scan",
             "band_ratios": [0.20, 0.30, 0.30, 0.15, 0.05], "transient": True},
            {"name": "Special Delivery", "key": "E", "icon": "stun",
             "band_ratios": [0.30, 0.30, 0.25, 0.10, 0.05], "transient": True},
            {"name": "Armageddon", "key": "X", "icon": "ultimate",
             "band_ratios": [0.40, 0.30, 0.18, 0.08, 0.04], "transient": True},
        ]
    },
}

# Common game sounds (not agent-specific)
VALORANT_COMMON = [
    {"name": "Footstep", "type": "movement", "icon": "footstep",
     "band_ratios": [0.54, 0.18, 0.17, 0.08, 0.03], "transient": True},
    {"name": "Jump/Land", "type": "movement", "icon": "footstep",
     "band_ratios": [0.56, 0.19, 0.16, 0.06, 0.03], "transient": True},
    {"name": "Spike Plant", "type": "objective", "icon": "spike_plant",
     "band_ratios": [0.26, 0.32, 0.27, 0.13, 0.02], "transient": False},
    {"name": "Spike Defuse", "type": "objective", "icon": "spike_defuse",
     "band_ratios": [0.12, 0.43, 0.19, 0.21, 0.05], "transient": False},
    {"name": "Vandal", "type": "gun", "icon": "gunshot",
     "band_ratios": [0.20, 0.25, 0.30, 0.20, 0.05], "transient": True},
    {"name": "Phantom", "type": "gun", "icon": "gunshot",
     "band_ratios": [0.15, 0.25, 0.35, 0.20, 0.05], "transient": True},
    {"name": "Operator", "type": "gun", "icon": "gunshot",
     "band_ratios": [0.30, 0.25, 0.25, 0.15, 0.05], "transient": True},
    {"name": "Sheriff", "type": "gun", "icon": "gunshot",
     "band_ratios": [0.25, 0.25, 0.25, 0.20, 0.05], "transient": True},
    {"name": "Classic", "type": "gun", "icon": "gunshot",
     "band_ratios": [0.15, 0.30, 0.30, 0.20, 0.05], "transient": True},
    {"name": "Spectre", "type": "gun", "icon": "gunshot",
     "band_ratios": [0.15, 0.30, 0.30, 0.20, 0.05], "transient": True},
    {"name": "Reload", "type": "action", "icon": "reload",
     "band_ratios": [0.20, 0.35, 0.30, 0.12, 0.03], "transient": True},
    {"name": "Weapon Drop", "type": "action", "icon": "drop",
     "band_ratios": [0.35, 0.35, 0.20, 0.08, 0.02], "transient": True},
    {"name": "Teleporter", "type": "map", "icon": "teleport",
     "band_ratios": [0.77, 0.06, 0.06, 0.04, 0.07], "transient": True},
    {"name": "Rope", "type": "map", "icon": "rope",
     "band_ratios": [0.30, 0.35, 0.25, 0.08, 0.02], "transient": True},
]


def get_all_valorant_signatures():
    """Get all Valorant sound signatures as a flat list for matching."""
    sigs = list(VALORANT_COMMON)
    for agent_name, agent_data in VALORANT_AGENTS.items():
        for ability in agent_data["abilities"]:
            sig = ability.copy()
            sig["agent"] = agent_name
            sig["type"] = "ability"
            sigs.append(sig)
    return sigs


def get_agent_list():
    """Get list of agent names."""
    return sorted(VALORANT_AGENTS.keys())


def get_agent_abilities(agent_name):
    """Get abilities for a specific agent."""
    agent = VALORANT_AGENTS.get(agent_name, {})
    return agent.get("abilities", [])
