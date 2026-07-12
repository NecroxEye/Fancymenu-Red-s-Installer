import os
import sys
import time
import zipfile
import threading
import subprocess
import concurrent.futures
from pathlib import Path
import ctypes

try:
    import requests
except ImportError:
    print("Required package 'requests' was not found.")
    print("Installing requests...\n")

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "requests"
        ])
    except Exception:
        print("\nFailed to install 'requests'.")
        print("Please install it manually with:")
        print("python -m pip install requests")
        input("\nPress ENTER to exit...")
        sys.exit(1)

    import requests


try:
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)

    mode = ctypes.c_uint()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    kernel32.SetConsoleMode(handle, mode.value | 0x0004)
except Exception:
    pass

# ============================================================
# CONFIGURATION
# ============================================================

CURRENT_VERSION = "3.0.1"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "NecroxEye/Fancymenu-Red-s-Installer/main/version.txt"
)

SCRIPT_URL = (
    "https://raw.githubusercontent.com/"
    "NecroxEye/Fancymenu-Red-s-Installer/"
    "main/Red%27sClientSide_InstallerX.py"
)

MINECRAFT_VERSION = "1.21.1"
LOADER = "neoforge"

MAX_DOWNLOAD_THREADS = 12
MAX_RETRIES = 3


BASE_FOLDER = Path(__file__).parent
OUTPUT_FOLDER = BASE_FOLDER / "ClientSideMods"

MOD_FOLDER = None
FANCYMENU_EXTRACT_FOLDER = None

# ============================================================
# FANCYMENU TEMPLATE
# ============================================================

FANCYMENU_URL = "https://github.com/NecroxEye/Fancymenu-Red-s-Installer/releases/download/fancymenu/fancymenu.zip"

INSTALL_FANCYMENU_TEMPLATE = False

# =============================================================

def _select_from_instances(title, instances):
    print(f"\n{title}\n")
    for i,(n,_) in enumerate(instances,1):
        print(f"{i}. {n}")
    while True:
        c=input("> ").strip()
        if c.isdigit() and 1<=int(c)<=len(instances):
            return instances[int(c)-1][1]
        print("Invalid choice.")

def find_curseforge_instances():
    root = Path.home() / "curseforge" / "minecraft" / "Instances"

    if not root.exists():
        return []

    instances = []

    for instance in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not instance.is_dir():
            continue

        mods = instance / "mods"
        mods.mkdir(parents=True, exist_ok=True)

        instances.append((instance.name, mods))

    return instances

def find_prism_instances():
    roots=[
        Path(os.getenv("APPDATA",""))/"PrismLauncher"/"instances",
    ]
    out=[]
    for r in roots:
        if r.exists():
            for d in r.iterdir():
                mods=d/".minecraft"/"mods"
                if d.is_dir():
                    mods.mkdir(parents=True,exist_ok=True)
                    out.append((d.name,mods))
    return out

def choose_install_location():

    global OUTPUT_FOLDER, MOD_FOLDER, FANCYMENU_EXTRACT_FOLDER

    while True:

        print("\nWhere do you want to install the mods?\n")
        print("1. Vanilla (.minecraft)")
        print("2. CurseForge")
        print("3. Prism Launcher")
        print("4. Custom Folder")
        print("5. ClientSideMods Folder")

        c = input("> ").strip()


        # ==========================================
        # VANILLA
        # ==========================================

        if c == "1":

            minecraft_folder = (
                Path(os.getenv("APPDATA"))
                /
                ".minecraft"
            )

            MOD_FOLDER = minecraft_folder / "mods"

            FANCYMENU_EXTRACT_FOLDER = (
                minecraft_folder
                /
                "config"
            )

            OUTPUT_FOLDER = MOD_FOLDER

            MOD_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )

            FANCYMENU_EXTRACT_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )

            cleanup_clientsidemods()

            return


        # ==========================================
        # CURSEFORGE
        # ==========================================

        elif c == "2":

            inst = find_curseforge_instances()

            if not inst:

                print(
                    "No CurseForge instances found."
                )

                continue


            selected_mods_folder = _select_from_instances(
                "Choose a CurseForge instance:",
                inst
            )


            # find_curseforge_instances() returns:
            # InstanceName/mods
            MOD_FOLDER = selected_mods_folder


            # Therefore .parent is:
            # InstanceName/
            instance_folder = (
                selected_mods_folder.parent
            )


            FANCYMENU_EXTRACT_FOLDER = (
                instance_folder
                /
                "config"
            )


            OUTPUT_FOLDER = MOD_FOLDER


            MOD_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )


            FANCYMENU_EXTRACT_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )


            cleanup_clientsidemods()

            return


        # ==========================================
        # PRISM LAUNCHER
        # ==========================================

        elif c == "3":

            inst = find_prism_instances()

            if not inst:

                print(
                    "No Prism Launcher instances found."
                )

                continue


            selected_mods_folder = _select_from_instances(
                "Choose a Prism instance:",
                inst
            )


            # find_prism_instances() returns:
            # InstanceName/.minecraft/mods
            MOD_FOLDER = selected_mods_folder


            # Therefore .parent is:
            # InstanceName/.minecraft/
            minecraft_folder = (
                selected_mods_folder.parent
            )


            FANCYMENU_EXTRACT_FOLDER = (
                minecraft_folder
                /
                "config"
            )


            OUTPUT_FOLDER = MOD_FOLDER


            MOD_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )


            FANCYMENU_EXTRACT_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )


            cleanup_clientsidemods()

            return


        # ==========================================
        # CUSTOM FOLDER
        # ==========================================

        elif c == "4":

            selected_folder = Path(
                input(
                    "Folder path: "
                ).strip()
            )


            selected_folder.mkdir(
                parents=True,
                exist_ok=True
            )


            # Mods go inside:
            # SelectedFolder/ClientSideMods/
            MOD_FOLDER = (
                selected_folder
                /
                "ClientSideMods"
            )


            # FancyMenu becomes:
            # SelectedFolder/fancymenu/
            FANCYMENU_EXTRACT_FOLDER = (
                selected_folder
            )


            OUTPUT_FOLDER = MOD_FOLDER


            MOD_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )


            cleanup_clientsidemods()

            return


        # ==========================================
        # CLIENTSIDEMODS BESIDE INSTALLER
        # ==========================================

        elif c == "5":

            # Mods:
            # InstallerFolder/ClientSideMods/
            MOD_FOLDER = (
                BASE_FOLDER
                /
                "ClientSideMods"
            )


            # FancyMenu:
            # InstallerFolder/fancymenu/
            FANCYMENU_EXTRACT_FOLDER = (
                BASE_FOLDER
            )


            OUTPUT_FOLDER = MOD_FOLDER


            MOD_FOLDER.mkdir(
                parents=True,
                exist_ok=True
            )


            return


        print("Invalid choice.")

# ============================================================
# ADD YOUR MODS HERE
# ============================================================

PERFORMANCE_MODS = [
    {
        "name": "Entity Culling",
        "url": "https://modrinth.com/mod/entityculling"
    },
    {
        "name": "Architectury Api",
        "url": "https://modrinth.com/mod/architectury-api"
    },
    {
        "name": "Particle Core",
        "url": "https://modrinth.com/mod/particle-core"
    },
    {
        "name": "Clientside Crafting",
        "url": "https://modrinth.com/mod/clientsidecrafting"
    },
    {
        "name": "No telemetry",
        "url": "https://modrinth.com/mod/no-telemetry"
    },
    {
        "name": "Ixeris",
        "url": "https://modrinth.com/mod/ixeris"
    },
    {
        "name": "Language Reload",
        "url": "https://modrinth.com/mod/neo-language-reload"
    },
    {
        "name": "More Culling",
        "url": "https://modrinth.com/mod/moreculling"
    },
    {
        "name": "Enhanced Block Entity",
        "url": "https://modrinth.com/mod/enhanced-block-entities-neoforged"
    },
    {
        "name": "No chat reports",
        "url": "https://modrinth.com/mod/no-chat-reports"
    },
    {
        "name": "borderless mining",
        "url": "https://modrinth.com/mod/borderless-mining"
    },
    {
        "name": "Immediately Fast",
        "url": "https://modrinth.com/mod/immediatelyfast"
    },
    {
        "name": "Scalable lux",
        "url": "https://modrinth.com/mod/scalablelux"
    },
    {
        "name": "Ferrite Core",
        "url": "https://modrinth.com/mod/ferrite-core"
    },
    {
        "name": "Lithium",
        "url": "https://modrinth.com/mod/lithium"
    },
    {
        "name": "Modern Fix",
        "url": "https://modrinth.com/mod/modernfix"
    },
    {
        "name": "Noisium",
        "url": "https://modrinth.com/mod/noisiumforked"
    },
    {
        "name": "Dynamic FPS",
        "url": "https://modrinth.com/mod/dynamic-fps"
    }
]


VISUAL_MODS = [
    {
        "name": "First Person Model",
        "url": "https://modrinth.com/mod/first-person-model"
    },
    {
        "name": "3D Skin Layer",
        "url": "https://modrinth.com/mod/3dskinlayers"
    },
    {
        "name": "Fancy Block Particles",
        "url": "https://modrinth.com/mod/fbp-renewed"
    },
    {
        "name": "Vintage Animations",
        "url": "https://modrinth.com/mod/vintage-animations"
    },
    {
        "name": "Immersive hotbar",
        "url": "https://modrinth.com/mod/immersive-hotbar"
    },
    {
        "name": "Fanct Toasts",
        "url": "https://modrinth.com/mod/fancy-toasts"
    },
    {
        "name": "Fancy World Animations",
        "url": "https://modrinth.com/mod/fwa"
    },
    {
        "name": "Model Gap Fix",
        "url": "https://modrinth.com/mod/modelfix"
    },
    {
        "name": "Screenshot viewer",
        "url": "https://modrinth.com/mod/screenshot-viewer"
    },
    {
        "name": "Tiny Item Animation",
        "url": "https://modrinth.com/mod/tiny-item-animations"
    },
    {
        "name": "Distant Horizon",
        "url": "https://modrinth.com/mod/distanthorizons"
    },
    {
        "name": "ETF (Entity Texture Features)",
        "url": "https://modrinth.com/mod/entitytexturefeatures"
    },
    {
        "name": "RMF Entity Model Features",
        "url": "https://modrinth.com/mod/entity-model-features"
    },
    {
        "name": "ESF Entity Sound Features",
        "url": "https://modrinth.com/mod/esf"
    },
    {
        "name": "Better 3Rd Person",
        "url": "https://modrinth.com/mod/better-third-person"
    },
    {
        "name": "Item Highlighter",
        "url": "https://modrinth.com/mod/item-highlighter"
    },
    {
        "name": "Pickup Notifier",
        "url": "https://modrinth.com/mod/pick-up-notifier"
    },
    {
        "name": "Durability Tooltip",
        "url": "https://modrinth.com/mod/durability-tooltip"
    },
    {
        "name": "Item Borders",
        "url": "https://modrinth.com/mod/item-borders"
    },
    {
        "name": "Legendary Tooltips",
        "url": "https://modrinth.com/mod/legendary-tooltips"
    },
    {
        "name": "Camera Overhaul",
        "url": "https://modrinth.com/mod/cameraoverhaul"
    },
    {
        "name": "Chat Animation",
        "url": "https://modrinth.com/mod/chatanimation"
    },
    {
        "name": "Inventory Particles",
        "url": "https://modrinth.com/mod/inventory-particles"
    },
    {
        "name": "Enhanced Toolips",
        "url": "https://modrinth.com/mod/enhancedtooltips"
    },
    {
        "name": "Inventory Interactions",
        "url": "https://modrinth.com/mod/inventory-interactions"
    },
    {
        "name": "Smooth Swamping",
        "url": "https://modrinth.com/mod/smooth-swapping"
    },
    {
        "name": "SmoothGUI",
        "url": "https://modrinth.com/mod/smooth-gui"
    },
    {
        "name": "Cinematic Zoom",
        "url": "https://modrinth.com/mod/cinematiczoom"
    },
    {
        "name": "Subtle Effects",
        "url": "https://modrinth.com/mod/subtle-effects"
    },
    {
        "name": "Reactive Music",
        "url": "https://modrinth.com/mod/reactive-music"
    },
    {
        "name": "Immersive UI",
        "url": "https://modrinth.com/mod/immersive-ui"
    },
    {
        "name": "AppleSkin",
        "url": "https://modrinth.com/mod/appleskin"
    },
    {
        "name": "Leave my Bars Alone",
        "url": "https://modrinth.com/mod/leave-my-bars-alone"
    },
    {
        "name": "Better Animation Collection",
        "url": "https://modrinth.com/mod/better-animations-collection"
    },
    {
        "name": "Punchy FPA",
        "url": "https://modrinth.com/mod/punchy-fpa"
    },
    {
        "name": "Better Ping Display",
        "url": "https://modrinth.com/mod/better-ping-display"
    },
    {
        "name": "Minecraft Cursor",
        "url": "https://modrinth.com/mod/minecraft-cursor"
    },
    {
        "name": "Loot Journal",
        "url": "https://modrinth.com/mod/loot-journal"
    },
    {
        "name": "Dmg Numbers",
        "url": "https://modrinth.com/mod/damagenumbers"
    },
    {
        "name": "Helditem Tooltips",
        "url": "https://modrinth.com/mod/held-item-tooltips"
    },
    {
        "name": "Effect Insights",
        "url": "https://modrinth.com/mod/effect-insights"
    },
    {
        "name": "Presence Footstep",
        "url": "https://modrinth.com/mod/pf-neoforge"
    },
    {
        "name": "Tooltip Overhaul",
        "url": "https://modrinth.com/mod/tooltip-overhaul"
    },
    {
        "name": "Medieval Paintings",
        "url": "https://modrinth.com/mod/medieval-paintings"
    },
    {
        "name": "Traveler's Title",
        "url": "https://modrinth.com/mod/travelers-titles"

    },
    {
        "name": "Auroras",
        "url": "https://modrinth.com/mod/auroras/"
    }
]


GAMEPLAY_MODS = [
    {
        "name": "Resourcify",
        "url": "https://modrinth.com/mod/resourcify"
    },
    {
        "name": "JEI Just Enough Items",
        "url": "https://modrinth.com/mod/jei"
    },
    {
        "name": "Fast ip ping",
        "url": "https://modrinth.com/mod/fast-ip-ping"
    },
    {
        "name": "Sound Physics Perfected",
        "url": "https://modrinth.com/mod/sound-physics-perfected"
    },
    {
        "name": "Raised",
        "url": "https://modrinth.com/mod/raised"
    },
    {
        "name": "better mc screenshots",
        "url": "https://modrinth.com/mod/better-mc-screenshots"
    },
    {
        "name": "Better Climbing",
        "url": "https://modrinth.com/mod/better-climbing"
    },
    {
        "name": "Cur Through",
        "url": "https://modrinth.com/mod/cut-through"
    },
    {
        "name": "Mouse Tweaks",
        "url": "https://modrinth.com/mod/mouse-tweaks"
    },
    {
        "name": "Controlling",
        "url": "https://modrinth.com/mod/controlling"
    },
    {
        "name": "Inventory Profiles Next",
        "url": "https://modrinth.com/mod/inventory-profiles-next"
    }
]


OPTIONAL_MODS = [
    {
        "name": "Install Embeddium + Shader Support?",
        "group": "renderer",
        "mods": [
            {
                "name": "Embeddium",
                "url": "https://modrinth.com/mod/embeddium"
            },
            {
                "name": "Rubidium Extra",
                "url": "https://modrinth.com/mod/rubidium-extra"
            },
            {
                "name": "NEOculus",
                "url": "https://modrinth.com/mod/neoculus"
            }
        ]
    },

    {
        "name": "Install Sodium + Iris Support?",
        "group": "renderer",
        "mods": [
            {
                "name": "Sodium",
                "url": "https://modrinth.com/mod/sodium"
            },
            {
                "name": "Iris Shaders",
                "url": "https://modrinth.com/mod/iris"
            }
        ]
    },

    {
        "name": "Install JourneyMap?",
        "group": "minimap",
        "mods": [
            {
                "name": "JourneyMap",
                "url": "https://modrinth.com/mod/journeymap"
            }
        ]
    },

    {
        "name": "Install Xaero's Map?",
        "group": "minimap",
        "mods": [
            {
                "name": "Xaero's Minimap",
                "url": "https://modrinth.com/mod/xaeros-minimap"
            },
            {
                "name": "Xaero's World Map",
                "url": "https://modrinth.com/mod/xaeros-world-map"
            }
        ]
    },

    {
        "name": "Install Forgematica?",
        "mods": [
            {
                "name": "Forgematica",
                "url": "https://modrinth.com/mod/forgematica"
            }
        ]
    },

    {
        "name": "Epic Death Screen",
        "group": "Death Screen",
        "mods": [
            {
                "name": "Epic Death Screen",
                "url": "https://modrinth.com/mod/epic-death-screen"
            }
        ]
    },
    
        {
        "name": "Install Undertale Death Screen?",
        "group": "Death Screen",
        "mods": [
            {
                "name": "Undertale Death Screen",
                "url": "https://modrinth.com/mod/undertale-death-screen"
            }
        ]
    },

    {
        "name": "Install Chest Helper?",
        "mods": [
            {
                "name": "Chest Helper",
                "url": "https://modrinth.com/mod/chest-helper"
            }
        ]
    },

    {
        "name": "Install Fancy Menu + Addons?",
        "fancymenu": True,
        "mods": [
            {
                "name": "FancyMenu",
                "url": "https://modrinth.com/mod/fancymenu"
            },
            {
                "name": "Drippy Loading Screen",
                "url": "https://modrinth.com/mod/drippy-loading-screen"
            },
            {
                "name": "SpiffyHUD",
                "url": "https://modrinth.com/mod/spiffyhud"
            },
            {
                "name": "MCEF",
                "url": "https://modrinth.com/mod/mcef"
            },
            {
                "name": "Startup Sound",
                "url": "https://modrinth.com/mod/startup-sound"
            }
        ]
    },

    {
        "name": "Install Fancy Message? Telling You Random Stuff As In A Story",
        "mods": [
            {
                "name": "Fancy Message",
                "url": "https://modrinth.com/mod/fancy-messages/"
            }
        ]
    },

    {
        "name": "Install PhysicsMod?",
        "mods": [
            {
                "name": "PhysicsMod",
                "url": "https://modrinth.com/mod/physicsmod"
            }
        ]
    }
]
    

    

# ============================================================
# COLORS
# ============================================================

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

BAR_WIDTH = 30



# ============================================================
# INSTALL STEPS
# ============================================================

CURRENT_STEP = 0

CURRENT_MOD = ""
TOTAL_DOWNLOADS = 0

CURRENT_STATUS = "Idle"

SPINNER_INDEX = 0
SPINNER_CHARS = [
    "|",
    "/",
    "-",
    "\\"
]


def step(title):

    global CURRENT_STEP
    global TOTAL_DOWNLOADS
    global CURRENT_MOD

    CURRENT_STEP += 1

    print()

    print(CYAN + "=" * 60)
    print(f" STEP {CURRENT_STEP}")
    print("=" * 60)
    print(title)
    print("=" * 60 + RESET)
    print()

    CURRENT_MOD = ""
    TOTAL_DOWNLOADS = 0
    
# ============================================================
# STATISTICS
# ============================================================

stats = {
    "installed": 0,
    "skipped": 0,
    "failed": 0,
    "completed": 0,
    "start": 0,

    "downloaded_bytes": 0,
    "total_bytes": 0,

    "speed": 0,
    "eta": 0
}

progress_lock = threading.Lock()


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "NeoForge-Client-Mod-Installer"
})

# API caches
project_cache = {}
version_cache = {}


# ============================================================
# AUTO UPDATER
# ============================================================

def check_for_updates():

    print(CYAN + "Checking for updates..." + RESET)

    try:
        response = requests.get(
            VERSION_URL,
            timeout=10
        )

        response.raise_for_status()

        latest_version = response.text.strip()

        if latest_version == CURRENT_VERSION:
            print(
                GREEN +
                f"Installer is up to date. Version {CURRENT_VERSION}"
                +
                RESET
            )
            return


        print(
            YELLOW +
            f"New version found: {latest_version}"
            +
            RESET
        )

        print(
            CYAN +
            "Downloading update..."
            +
            RESET
        )


        response = requests.get(
            SCRIPT_URL,
            timeout=60
        )

        response.raise_for_status()

        new_script = response.content


        # Basic validation
        if len(new_script) < 1000:
            raise Exception(
                "Downloaded update is unexpectedly small."
            )


        current_script = Path(__file__).resolve()

        temp_script = current_script.with_suffix(".update")


        with open(temp_script, "wb") as f:
            f.write(new_script)


        # Make sure it looks like a Python script
        with open(temp_script, "r", encoding="utf-8") as f:
            content = f.read()

        if "def main()" not in content:
            temp_script.unlink()
            raise Exception(
                "Downloaded update is not a valid installer script."
            )


        print(
            GREEN +
            "Update downloaded successfully!"
            +
            RESET
        )


        # Replace old script
        os.replace(
            temp_script,
            current_script
        )


        print(
            GREEN +
            "Installer updated successfully!"
            +
            RESET
        )

        print(
            CYAN +
            "Restarting installer..."
            +
            RESET
        )


        time.sleep(1)


        os.execv(
            sys.executable,
            [
                sys.executable,
                str(current_script)
            ]
        )


    except Exception as e:

        print(
            YELLOW +
            f"Could not check for updates: {e}"
            +
            RESET
        )

        print(
            YELLOW +
            "Continuing with the current version..."
            +
            RESET
        )

# ============================================================
# BASIC FUNCTIONS
# ============================================================

def banner():

    print(CYAN + """
==========================================
 NeoForge 1.21.1 Client Mod Installer
==========================================
""" + RESET)



def create_folders():

    if OUTPUT_FOLDER:
        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    if MOD_FOLDER:
        MOD_FOLDER.mkdir(parents=True, exist_ok=True)



def clean_name(url):

    return url.rstrip("/").split("/")[-1]



def pause():

    input("\nPress ENTER to continue...")


def clear_console():

    os.system("cls" if os.name == "nt" else "clear")

def format_size(size):

    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"

    return f"{size / (1024 * 1024 * 1024):.2f} GB"

def calculate_speed():

    elapsed = time.time() - stats["start"]

    if elapsed <= 0:
        return 0

    return stats["downloaded_bytes"] / elapsed

def calculate_eta():

    speed = calculate_speed()

    remaining = (
        stats["total_bytes"]
        -
        stats["downloaded_bytes"]
    )

    if speed <= 0:
        return "Calculating..."

    seconds = remaining / speed

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    if minutes > 0:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"

def get_spinner():

    global SPINNER_INDEX

    char = SPINNER_CHARS[SPINNER_INDEX]

    SPINNER_INDEX += 1

    if SPINNER_INDEX >= len(SPINNER_CHARS):
        SPINNER_INDEX = 0

    return char


def update_dashboard(completed, total):

    clear_console()

    print(
        CYAN +
        draw_progress(
            completed,
            total
        )
        +
        RESET
    )



def cleanup_clientsidemods():
    folder=BASE_FOLDER/"ClientSideMods"
    if MOD_FOLDER==folder:return
    if folder.exists():
        try:
            if not any(folder.iterdir()): folder.rmdir()
        except Exception: pass

def show_install_location():
    print(CYAN+"\n============================================================\n Installation Destination\n============================================================\n"+RESET)
    print(f"Folder   : {MOD_FOLDER}")
    print(f"Minecraft: {MINECRAFT_VERSION}")
    print(f"Loader   : {LOADER.capitalize()}")
    print(CYAN+"="*60+RESET)
    print()


def draw_progress(completed, total):

    if total == 0:
        total = 1

    percent = completed / total

    width = 35

    filled = int(width * percent)

    bar = "█" * filled + "░" * (width - filled)

    remaining = total - completed

    return f"""
============================================================
 STEP 5/5 - Downloading Mods
============================================================

Progress

[{bar}] {percent * 100:5.1f}%

Installed : {stats['installed']}
Skipped   : {stats['skipped']}
Failed    : {stats['failed']}
Remaining : {remaining}

Downloaded: {format_size(stats["downloaded_bytes"])}
Speed     : {format_size(calculate_speed())}/s
ETA       : {calculate_eta()}

Status:
{CURRENT_STATUS} {get_spinner()}

Current:
{CURRENT_MOD}

============================================================
"""

# ============================================================
# MODRINTH API
# ============================================================

def get_project_from_url(url):

    slug = clean_name(url)

    if slug in project_cache:
        return project_cache[slug]

    api = f"https://api.modrinth.com/v2/project/{slug}"

    try:
        r = session.get(api, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        project_cache[slug] = data
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_version_files(project_id):

    if project_id in version_cache:
        return version_cache[project_id]

    url=(f"https://api.modrinth.com/v2/project/{project_id}/version")
    try:
        r=session.get(url,timeout=20)
        if r.status_code!=200:
            return None
        versions=r.json()
        for version in versions:
            if MINECRAFT_VERSION in version.get("game_versions",[]) and LOADER in version.get("loaders",[]):
                version_cache[project_id]=version
                return version
        for version in versions:
            if MINECRAFT_VERSION in version.get("game_versions",[]):
                version_cache[project_id]=version
                return version
    except Exception as e:
        print(f"Error: {e}")
    return None

def get_mod_dependencies(project_id):

    version = get_version_files(project_id)

    if not version:
        return []


    deps = []

    BLOCKED_DEPENDENCIES = [
        "P7dR8mSH",   # Fabric API (example ID)
    ]


    for dep in version.get("dependencies", []):

        if dep.get("dependency_type") == "required":

            if dep.get("project_id"):

                dependency_id = dep["project_id"]

                if dependency_id in BLOCKED_DEPENDENCIES:
                    print(
                        "Skipping blocked dependency:",
                        dependency_id
                    )
                    continue


                deps.append(
                    dependency_id
                )


    return deps



# ============================================================
# DEPENDENCY GRAPH
# ============================================================

def resolve_dependencies(project_ids):

    resolved = set()


    def scan(pid):

        if pid in resolved:
            return


        resolved.add(pid)


        for dep in get_mod_dependencies(pid):
            scan(dep)


    for project in project_ids:
        scan(project)


    return list(resolved)



# ============================================================
# CONVERT MOD URLS TO PROJECT IDS
# ============================================================

def collect_projects(mods):

    projects = []


    for mod in mods:

        project = get_project_from_url(
            mod["url"]
        )


        if project:

            projects.append(
                project["id"]
            )

        else:

            print(
                RED +
                f"Could not find {mod['url']}"
                +
                RESET
            )


    return projects
# ============================================================
# DOWNLOAD SYSTEM
# ============================================================

def get_download_information(project_id):

    version = get_version_files(project_id)

    if not version:
        return None

    files = version.get("files", [])

    if not files:
        return None

    file = files[0]

    return {
    "project_id": project_id,
    "version_id": version["id"],
    "version_number": version.get("version_number", ""),
    "filename": file["filename"],
    "url": file["url"],
    "size": file.get("size", 0)
    }



def download_file(data, index, total):

    filename = data["filename"]
    url = data["url"]

    global CURRENT_MOD
    global CURRENT_STATUS

    destination = MOD_FOLDER / filename


    with progress_lock:

        CURRENT_MOD = filename
        CURRENT_STATUS = "Checking"



    # Already exists
    if destination.exists():

        with progress_lock:

            stats["completed"] += 1
            stats["skipped"] += 1

            CURRENT_STATUS = "Already Installed"

            update_dashboard(
                stats["completed"],
                total
            )

        return



    for attempt in range(1, MAX_RETRIES + 1):

        temp_file = destination.with_suffix(".part")


        try:

            with progress_lock:

                CURRENT_MOD = filename
                CURRENT_STATUS = (
                    f"Downloading "
                    f"(Attempt {attempt}/{MAX_RETRIES})"
                )

                update_dashboard(
                    stats["completed"],
                    total
                )



            with session.get(
                url,
                stream=True,
                timeout=(10, 60)
            ) as response:


                if response.status_code != 200:

                    raise Exception(
                        f"HTTP {response.status_code}"
                    )



                last_update = time.time()



                with open(temp_file, "wb") as f:


                    for chunk in response.iter_content(
                        chunk_size=65536
                    ):


                        if chunk:

                            f.write(chunk)


                            with progress_lock:

                                stats["downloaded_bytes"] += len(chunk)



                            # Update dashboard every 0.3 seconds
                            if time.time() - last_update >= 1:


                                update_dashboard(
                                    stats["completed"],
                                    total
                                )


                                last_update = time.time()



            # Validate JAR file

            with open(temp_file, "rb") as f:


                if f.read(2) != b"PK":

                    raise Exception(
                        "Downloaded file is not a valid JAR"
                    )



            # Move finished file

            temp_file.replace(destination)



            with progress_lock:

                stats["installed"] += 1
                stats["completed"] += 1

                CURRENT_STATUS = "Installed"

                update_dashboard(
                    stats["completed"],
                    total
                )


            return



        except Exception as e:


            # Remove broken partial file

            if temp_file.exists():

                try:

                    temp_file.unlink()

                except:

                    pass



            with progress_lock:

                CURRENT_STATUS = (
                    f"Failed attempt "
                    f"{attempt}/{MAX_RETRIES}"
                )


                update_dashboard(
                    stats["completed"],
                    total
                )



            time.sleep(2)



    # All retries failed

    with progress_lock:

        stats["failed"] += 1
        stats["completed"] += 1

        CURRENT_STATUS = "Failed"

        update_dashboard(
            stats["completed"],
            total
        )


    time.sleep(1)



def download_all(project_ids):

    downloads = []


    for pid in project_ids:

        info = get_download_information(pid)

        if info:

            downloads.append(info)



    # Remove duplicate downloads
    unique = {}

    for d in downloads:

        unique[d["filename"]] = d


    downloads = list(unique.values())



    # Remove already installed mods
    downloads = filter_existing_downloads(downloads)



    # Calculate total download size
    stats["total_bytes"] = sum(
        d.get("size", 0)
        for d in downloads
    )



    total = len(downloads)

    global TOTAL_DOWNLOADS

    TOTAL_DOWNLOADS = total



    if total == 0:

        print(
            GREEN +
            "All selected mods are already installed."
            +
            RESET
        )

        return



    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_DOWNLOAD_THREADS
    ) as executor:


        jobs = []


        for i, item in enumerate(
            downloads,
            start=1
        ):


            jobs.append(
                executor.submit(
                    download_file,
                    item,
                    i,
                    total
                )
            )



        for job in jobs:

            job.result()


def filter_existing_downloads(downloads):

    clear_console()

    print(
        CYAN +
        "\nChecking existing mods..." +
        RESET
    )

    existing = {
        f.name.lower()
        for f in MOD_FOLDER.glob("*.jar")
    }

    filtered = []

    already = 0

    for d in downloads:

        if d["filename"].lower() in existing:

            already += 1
            stats["skipped"] += 1

        else:

            filtered.append(d)


    print(
        GREEN +
        f"\nAlready installed : {already}" +
        RESET
    )

    print(
        CYAN +
        f"Need to download : {len(filtered)}" +
        RESET
    )

    return filtered


# ============================================================
# MENU
# ============================================================

def choose_category():

    while True:

        print("""
=============================
 Choose Installation Type
=============================

1. Full Installation
2. Performance Only
3. Visual Only
4. Custom
5. Exit

""")


        choice = input("> ")


        if choice == "1":

            return (
                PERFORMANCE_MODS
                +
                VISUAL_MODS
                +
                GAMEPLAY_MODS
                +
                expand_optional_mods()
            )


        elif choice == "2":

            return PERFORMANCE_MODS


        elif choice == "3":

            return VISUAL_MODS


        elif choice == "4":

            return custom_menu()


        elif choice == "5":

            sys.exit()


def expand_optional_mods():

    global INSTALL_FANCYMENU_TEMPLATE

    selected = []
    selected_groups = set()

    for option in OPTIONAL_MODS:

        group = option.get("group")

        if group and group in selected_groups:
            continue

        answer = input(
            f"{option['name']} (Y/N): "
        )

        if answer.lower() == "y":

            if group:
                selected_groups.add(group)

            selected.extend(
                option["mods"]
            )

            if option.get("fancymenu"):

                template_answer = input(
                    "Install Red's FancyMenu Template? (Y/N): "
                )

                if template_answer.lower() == "y":
                    INSTALL_FANCYMENU_TEMPLATE = True

    return selected



def custom_menu():

    selected = []


    categories = [

        (
            "Performance",
            PERFORMANCE_MODS
        ),

        (
            "Visuals + Immersion",
            VISUAL_MODS
        ),

        (
            "Gameplay",
            GAMEPLAY_MODS
        )

    ]


    for name, mods in categories:

        if not mods:
            continue


        print(
            f"\nInstall {name}? (Y/N)"
        )


        answer = input("> ")


        if answer.lower() == "y":

            selected.extend(mods)



    selected.extend(
        expand_optional_mods()
    )


    return selected



# ============================================================
# INSTALL PROCESS
# ============================================================

def install_fancymenu_template():

    if FANCYMENU_EXTRACT_FOLDER is None:

        print(
            RED +
            "FancyMenu installation folder was not set."
            +
            RESET
        )

        return


    FANCYMENU_EXTRACT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )


    zip_path = (
        FANCYMENU_EXTRACT_FOLDER
        /
        "fancymenu.zip"
    )


    try:

        print(
            CYAN +
            "\nDownloading Red's FancyMenu Template..."
            +
            RESET
        )


        response = session.get(
            FANCYMENU_TEMPLATE_URL,
            timeout=60
        )


        response.raise_for_status()


        with open(
            zip_path,
            "wb"
        ) as f:

            f.write(
                response.content
            )


        # Make sure GitHub actually returned a ZIP
        if not zipfile.is_zipfile(
            zip_path
        ):

            raise Exception(
                "Downloaded file is not a valid ZIP."
            )


        print(
            CYAN +
            "Extracting FancyMenu Template..."
            +
            RESET
        )


        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_file:

            zip_file.extractall(
                FANCYMENU_EXTRACT_FOLDER
            )


        # Delete ZIP after extraction
        zip_path.unlink()


        print(
            GREEN +
            "Red's FancyMenu Template installed!"
            +
            RESET
        )


        print(
            GREEN +
            f"Location: {FANCYMENU_EXTRACT_FOLDER}"
            +
            RESET
        )


    except Exception as e:

        print(
            RED +
            f"Failed to install FancyMenu Template: {e}"
            +
            RESET
        )


        if zip_path.exists():

            try:
                zip_path.unlink()

            except Exception:
                pass

def install(mods):

    if not mods:

        print(
            RED +
            "No mods selected."
            +
            RESET
        )

        return


    step("Collecting Projects")


    projects = collect_projects(mods)


    step("Resolving Dependencies")


    projects = resolve_dependencies(
        projects
    )


    step("Downloading Mods")
    download_all(projects)

    if INSTALL_FANCYMENU_TEMPLATE:
        install_fancymenu_template()



# ============================================================
# SUMMARY
# ============================================================

def show_summary():

    elapsed = (
        time.time()
        -
        stats["start"]
    )


    print(CYAN + """
==========================================
 Installation Finished
==========================================
""" + RESET)

    global CURRENT_STATUS
    CURRENT_STATUS = "Finished"

    print(
        GREEN +
        f"Installed: {stats['installed']}"
        +
        RESET
    )


    print(
        YELLOW +
        f"Skipped: {stats['skipped']}"
        +
        RESET
    )


    print(
        RED +
        f"Failed: {stats['failed']}"
        +
        RESET
    )


    print(
        MAGENTA +
        f"Time: {elapsed:.2f} seconds"
        +
        RESET
    )


# ============================================================
# MAIN
# ============================================================

def main():

    stats["start"] = time.time()

    stats["installed"] = 0
    stats["skipped"] = 0
    stats["failed"] = 0
    stats["completed"] = 0

    global CURRENT_STATUS
    CURRENT_STATUS = "Installed"

    banner()

    choose_install_location()
    create_folders()

    step("Installation Information")

    show_install_location()

    step("Selecting Mods")
    mods = choose_category()

    install(mods)

    step("Finishing Installation")
    show_summary()


    print(GREEN)
    print("=" * 70)
    print("                    Thank You for Using")
    print("          Red's Client Side Mods Installer")
    print("=" * 70)
    print("I hope you enjoy the modpack and have an awesome")
    print("Minecraft adventure! If you have suggestions or")
    print("find any issues, feel free to let me know.")
    print("Discord: red.forrest")
    print("=" * 70)
    print(RESET)

    pause()


if __name__ == "__main__":

    check_for_updates()
    
    main()
