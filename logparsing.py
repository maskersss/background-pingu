#!/usr/bin/env python
# coding: utf-8

import requests
import re
from packaging import version

import re
import requests

def download_from_paste_ee_or_mclogs(link):
    # Check if it's a paste.ee link
    paste_ee_pattern = r'https://paste\.ee/(?:p/|d/)([a-zA-Z0-9]+)'
    paste_ee_match = re.search(paste_ee_pattern, link)
    if paste_ee_match:
        paste_id = paste_ee_match.group(1)
        direct_link = f'https://paste.ee/d/{paste_id}/0'
    else:
        # Check if it's an mclo.gs link
        mclogs_pattern = r'https://mclo\.gs/(\w+)'
        mclogs_match = re.search(mclogs_pattern, link)
        if mclogs_match:
            mclogs_id = mclogs_match.group(1)
            direct_link = f'https://api.mclo.gs/1/raw/{mclogs_id}'
        else:
            return None

    # Download text from direct link
    response = requests.get(direct_link)
    if response.status_code == 200:
        return response.text
    else:
        return None

def get_mods_from_log(log):
    # Find all lines that have [✔️] before a mod name
    pattern = re.compile(r'\[✔️\]\s+([^\[\]]+\.jar)')
    mods = pattern.findall(log)

    # Return list of mod names
    return mods

def get_mods_type(mods):
    # 0 - no mods, 1 - mods but no fabric mods, 2 - fabric mods but no mcsr, 3 - mcsr mods
    mcsr_mods = ['worldpreview','anchiale','sleepbackground','StatsPerWorld','z-buffer-fog',
                'tab-focus','setspawn','SpeedRunIGT','atum','standardsettings','forceport',
                'lazystronghold','antiresourcereload','extra-options','chunkcacher',
                'serverSideRNG','BiomeThreadLocalFix','peepopractice']
    fabric_mods = ['lithium','FabricProxy-Lite','krypton','sodium','voyager']
    if len(mods) == 0:
        return 0
    elif any(any(mcsr_mod in mod for mcsr_mod in mcsr_mods) for mod in mods):
        return 3
    elif any(any(fabric_mod in mod for fabric_mod in fabric_mods) for mod in mods):
        return 2
    else:
        return 1

def get_java_version(log): # returns a string like '19.0.2'
    # Find the line that contains "Checking Java version..."
    pattern = re.compile(r'Checking Java version\.\.\.\n(.*)\n')
    match = pattern.search(log)

    if match:
        # Extract the Java version from the next line
        version_line = match.group(1)
        pattern = re.compile(r'Java is version (\S+),')
        version_match = pattern.search(version_line)
        if version_match:
            return version_match.group(1)

    # If the Java version can't be found, return None
    return None

def get_major_java_version(java_version):
    if java_version:
        version_parts = java_version.split('.')
        if version_parts[0] != '1':
            return int(version_parts[0])
        else:
            return int(version_parts[1])

def get_minecraft_folder(log):
    # Find the line that contains "Minecraft folder is:"
    pattern = re.compile(r'Minecraft folder is:\n(.*)\n')
    match = pattern.search(log)

    if match:
        # Extract the folder location from the next line
        folder_line = match.group(1)
        return folder_line.strip()

    # If the folder location can't be found, return None
    return None

def get_OS(folder_location):
    if folder_location is None:
        return None
    if folder_location.startswith('/'):
        if len(folder_location) > 1 and folder_location[1].isupper():
            return 'MacOS'
        else:
            return 'Linux'
    else:
        return 'Windows'

def get_minecraft_version(log):
    # Find the line that contains "Params:"
    pattern = re.compile(r'Params:\n(.*?)\n', re.DOTALL)
    match = pattern.search(log)

    if match:
        # Extract the version value from the next line
        params_line = match.group(1)
        version_pattern = re.compile(r'--version (\S+)\s')
        version_match = version_pattern.search(params_line)
        if version_match:
            return version_match.group(1)

    # If the Minecraft version can't be found, return None
    return None

def extract_fabric_loader_version(log):
    pattern = re.compile(r'Loading Minecraft \S+ with Fabric Loader (\S+)')
    match = pattern.search(log)

    if match:
        return match.group(1)

    return None

def get_launcher(log):
    if log[:7] == 'MultiMC':
        return 'MultiMC'
    if log[:5] == 'Prism':
        return 'Prism'
    if log[:6] == 'PolyMC':
        return 'PolyMC'
    if log[:6] == 'ManyMC':
        return 'ManyMC'
    if log[:7] == 'UltimMC':
        return 'UltimMC'

def get_is_multimc_or_fork(launcher):
    return (launcher in ['MultiMC','Prism','PolyMC','ManyMC','UltimMC'])

def get_modloader(log):
    # Find the line that contains "Main Class:"
    pattern = re.compile(r'Main Class:\n(.*)\n')
    match = pattern.search(log)

    if match:
        # Extract the modloader from the next line
        main_class_line = match.group(1)
        if 'quilt' in main_class_line:
            return 'quilt'
        elif 'forge' in main_class_line:
            return 'forge'
        elif 'fabric' in main_class_line:
            return 'fabric'
        else:
            if "forge" in log.split("\nLibraries:\n", 1)[-1].split("\nNative libraries:\n", 1)[0]:
                return 'forge'
            else:
                return 'vanilla'

    # If the modloader cannot be determined, return None
    return None

def get_java_arguments(log):
    pattern = re.compile(r'Java Arguments:\n(.*?)\n', re.DOTALL)
    match = pattern.search(log)
    if match:
        arguments_line = match.group(1)
        arguments_line = arguments_line
        return arguments_line

def get_max_memory_allocation(log):
    # Find the line that contains "Java Arguments:"
    pattern = re.compile(r'Java Arguments:\n(.*?)\n', re.DOTALL)
    match = pattern.search(log)

    if match:
        # Extract the value after "-Xmx" from the next line
        arguments_line = match.group(1)
        memory_pattern = re.compile(r'-Xmx(\d+)m')
        memory_match = memory_pattern.search(arguments_line)
        if memory_match:
            return int(memory_match.group(1))

    # If the maximum memory allocation value can't be found, return None
    return None

def not_using_fabric(modloader,mods_type):
    # 0 - no mods, 1 - mods but no general mods, 2 - general mods but no mcsr, 3 - mcsr mods
    if modloader == 'forge':
        if mods_type <= 1:
            return "🟡 Note that using Forge isn't allowed for speedrunning. Type `!!fabric` for a guide on how to install fabric."
        else:
            return "🔴 You seem to be using Fabric mods, but you have Forge installed. Uninstall Forge and type `!!fabric` for a guide on how to install fabric."
    elif modloader == 'quilt':
        if mods_type <= 2:
            return "🟡 Note that using Quilt isn't allowed for speedrunning. Type `!!fabric` for a guide on how to install fabric."
        elif mods_type == 3:
            return "🔴 You seem to be using Fabric mods, but you have Quilt installed. Using Quilt is not allowed for speedrunning. Uninstall Quilt and type `!!fabric` for a guide on how to install fabric."
    elif modloader == 'vanilla':
        if mods_type == 3:
            return "🔴 Note that all speedrunning mods require having Fabric installed. Type `!!fabric` for a guide on how to install fabric."
        elif mods_type == 2:
            return "🔴 The mods you are using require having Fabric installed. Type `!!fabric` for a guide on how to install fabric."
        elif mods_type == 1:
            return "🟡 You aren't using a modloader. Type `!!fabric` for a guide on how to install fabric."

def should_use_prism(launcher, OS):
    if launcher == 'MultiMC' and OS == 'MacOS':
        return '🟡 If you use M1 or M2, it is recommended to use Prism Launcher instead of MultiMC.'
    
def need_java_17_plus(log, mods, major_java_version):
    needed_java_version = None
    output = ''
    if 'java.lang.UnsupportedClassVersionError' in log:
        pattern = re.compile(r'class file version (\d+\.\d+)')
        match = pattern.search(log)
        if match:
            needed_java_version = round(float(match.group(1)))-44
    if major_java_version and major_java_version < 17:
        java_17_mods = [mod for mod in mods if
                       'worldpreview-2.' in mod
                       or 'worldpreview-1.0' in mod
                       or 'antiresourcereload' in mod
                       or 'serverSideRNG' in mod
                       or 'setspawnmod' in mod
                       or 'peepopractice' in mod]
        if len(java_17_mods) >= 1:
            needed_java_version = 17
            output += f"🔴 You are using {'mods' if len(java_17_mods)>1 else 'a mod'} ({', '.join(java_17_mods)}) that require{'s' if len(java_17_mods)==1 else ''} using Java {needed_java_version}+."
            if any("mcsrranked" in mod for mod in mods):
                update_java = 0
            elif any("antiresourcereload" in mod for mod in java_17_mods):
                update_java = 1
            elif any("peepopractice" in mod for mod in java_17_mods):
                update_java = 1
            else:
                update_java = 0
            if update_java:
                output += '\nUse this guide to update your Java version: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.62ygxgaxcs5a>.'
            else:
                output += ' Delete them from your mods folder.'
                output += '(alternatively, you can use this guide to update your Java version: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.62ygxgaxcs5a>).'
    if 'Minecraft 1.18 Pre Release 2 and above require the use of Java 17' in log:
        output += f"🔴 You are playing on a Minecraft version that requires using Java 17+.\n"
        output += 'Use this guide to update your Java version: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.62ygxgaxcs5a>.'
    if output:
        return output
    else:
        pattern = re.compile(r'The requested compatibility level (JAVA_\d+) could not be set.')
        match = pattern.search(log)
        if match:
            needed_java_version = match.group(1).split('_')[1]
        if needed_java_version:
            return f"🔴 You need to use Java {needed_java_version}+. Use this guide to update your Java version: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.62ygxgaxcs5a>."

def using_32bit_java(log):
    if 'Your Java architecture is not matching your system architecture. You might want to install a 64bit Java version.' in log:
        return "🔴 You're using 32-bit Java. See here for help installing the correct version: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.62ygxgaxcs5a>."

def outdated_srigt_fabric_01415(mods, fabric_loader_version, minecraft_version):
    output = ''
    speedrunigt = [mod for mod in mods if 'SpeedRunIGT' in mod]
    if len(speedrunigt) > 1:
        return '🟢 You have several versions of SpeedRunIGT installed. You should delete the older ones.'
    if len(speedrunigt) == 0:
        return None
    if fabric_loader_version is None:
        return None
    speedrunigt = speedrunigt[0]
    pattern = re.compile(r'-(\d+(?:\.\d+)?)\+')
    match = pattern.search(speedrunigt)
    if match:
        speedrunigt = match.group(1)
        if (version.parse(speedrunigt) < version.parse('13.3')
        and version.parse(fabric_loader_version) > version.parse('0.14.14')):
            output += "🔴 You're using an old version of SpeedrunIGT that is incompatible with Fabric Loader 0.14.14+. You should delete the one you have and download the latest one from https://redlime.github.io/SpeedRunIGT/"
            if minecraft_version != '1.16.1':
                output += '\nAlternatively, you can try using Fabric Loader 0.14.14.'
    if output:
        return output

def outdated_fabric_loader(fabric_loader_version, mods):
    if fabric_loader_version is None:
        return None
    elif version.parse(fabric_loader_version) < version.parse('0.14.0'):
        if any('mcsrranked' for mod in mods):
            return f"{'🔴' if any('mcsrranked' in mod for mod in mods) else '🟠'} You're using an old version of Fabric Loader. You should update it. Type `!!fabric` for instructions on how to do it."
    elif version.parse(fabric_loader_version) < version.parse('0.14.14'):
        return "🟡 You're using an old version of Fabric Loader. You should update it. Type `!!fabric` for instructions on how to do it."
    elif fabric_loader_version == '0.14.15' or fabric_loader_version == '0.14.16':
        return "🔴 You're using an old version of Fabric Loader. You should update it. Type `!!fabric` for instructions on how to do it."

def not_enough_ram_or_rong_sodium(max_memory_allocation, OS, mods, log, java_arguments):
    output = ''
    if max_memory_allocation:
        if (max_memory_allocation < (1200 if ('shenandoah' in java_arguments) else 1900)) and ('OutOfMemoryError' in log):
            output += '🔴 You likely have too little RAM allocated. Check out <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.y78pfyby3w9b> for a guide on how to fix it.\n'
        elif max_memory_allocation < (880 if ('shenandoah' in java_arguments) else 1200):
            output += '🟠 You likely have too little RAM allocated. Check out <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.y78pfyby3w9b> for a guide on how to fix it.\n'
        elif max_memory_allocation < (1200 if ('shenandoah' in java_arguments) else 1800):
            output += '🟡 You likely have too little RAM allocated. Check out <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.y78pfyby3w9b> for a guide on how to fix it.\n'
        if max_memory_allocation > 4500:
            output += '🟠 You likely have too much RAM allocated. Check out <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.y78pfyby3w9b> for a guide on how to fix it.\n'
        elif max_memory_allocation > 3100:
            output += '🟡 You likely have too much RAM allocated. Check out <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.y78pfyby3w9b> for a guide on how to fix it.\n'
        if OS == 'MacOS' and (('sodium-1.16.1-v1.jar' in mods) or ('sodium-1.16.1-v2.jar' in mods)):
            output += "🟠 You seem to be using a version of Sodium that has a memory leak on MacOS. Delete the one you have and download <https://github.com/Minecraft-Java-Edition-Speedrunning/mcsr-sodium-mac-1.16.1/releases/tag/latest> instead.\n"
    if output:
        return output.rstrip("\n")
    elif 'OutOfMemoryError' in log:
        return '🔴 You likely either have too little RAM allocated, or experienced a memory leak. Check out <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.y78pfyby3w9b> and <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.pmch2xu1p6ce>.'

def onedrive(minecraft_folder,launcher):
    if minecraft_folder and ('OneDrive' in minecraft_folder):
        return f"🟡 Your {launcher if launcher else 'launcher'} folder is located in OneDrive. OneDrive can mess with your game files to save space, and this often leads to crashes. You should move it out to a different folder, and may need to reinstall {launcher if launcher else 'the launcher'}."

def hs_err_pid(log, mods):
    output = ''
    if ('A fatal error has been detected by the Java Runtime Environment' in log
        or 'EXCEPTION_ACCESS_VIOLATION' in log):
        output += '''🟠 This crash may be caused by one of the following:
- Concurrently running programs, such as OBS and Discord, that use the same graphics card as the game.
 - Try using window capture instead of game capture in OBS.
 - Try disabling hardware acceleration in Discord.\n'''
        if any("SpeedRunIGT" in mod for mod in mods):
            output += '- A compatibility issue between SpeedrunIGT, Intel Graphics and OpenGL. Enable “safe font mode” in SpeedrunIGT options. If the game crashes before you can access that menu, delete .minecraft/speedrunigt.\n'
        output += "- Driver issues. Check if your drivers are updated, and update them or downgrade them if they're already updated."
    if output:
        return output.rstrip("\n")

def using_phosphor(mods, minecraft_version):
    if any("phosphor" in mod for mod in mods):
        if any("starlight" in mod for mod in mods):
            return '🔴 Phosphor and Starlight are incompatible. You should delete Phosphor from your mods folder.'
        elif minecraft_version != '1.12.2':
            output = "🟡 You're using Phosphor. Starlight is much better than Phosphor, you should use it instead. "
            if minecraft_version == '1.16.1':
                output += "You can download it here: <https://github.com/PaperMC/Starlight/releases/download/1.0.0-RC2/starlight-fabric-1.0.0-RC2-1.16.x.jar>"
            elif minecraft_version == '1.16.5':
                output += "You can download it here: <https://github.com/PaperMC/Starlight/releases/download/1.0.0-RC2/starlight-forge-1.0.0-RC2-1.16.5.jar>"
            elif len(minecraft_version)<4:
                output += "<@695658634436411404> huh1"
            elif float(minecraft_version[:4])>1.16:
                output += "You can download it here: <https://modrinth.com/mod/starlight/versions>"
            elif minecraft_version[:4] == '1.15':
                output += "You can download it here: <https://github.com/dariasc/Starlight/releases/tag/1.15%2F1.0.0-alpha>"
            else:
                output += "<@695658634436411404> huh2"
            return output

def failed_to_download_assets(log):
    if 'Instance update failed because: Failed to download the assets index:' in log:
        return '🔴 Try restarting your PC and then launching the instance again.'

def id_range_exceeded(log):
    if 'java.lang.RuntimeException: Invalid id 4096 - maximum id range exceeded.' in log:
        return "🔴 You've exceeded the hardcoded ID Limit. Remove some mods, or install [JustEnoughIDs](<https://www.curseforge.com/minecraft/mc-mods/jeid>)"

def multimc_in_program_files(minecraft_folder):
    if minecraft_folder and ('C:/Program Files' in minecraft_folder):
        return '🟡 Your MultiMC installation is in `Program Files`. It is generally not recommended, and could cause issues. Consider moving it to a different location.'

def macos_too_new_java(log):
    if "Terminating app due to uncaught exception 'NSInternalInconsistencyException', reason: 'NSWindow drag regions should only be invalidated on the Main Thread!'" in log:
        return "🔴 You are using too new a Java version. Please follow the steps on this wiki page to install 8u241: <https://github.com/MultiMC/MultiMC5/wiki/Java-on-macOS>. You don't need to uninstall the other Java version."

def forge_too_new_java(log):
    if 'java.lang.ClassCastException: class jdk.internal.loader.ClassLoaders$AppClassLoader cannot be cast to class java.net.URLClassLoader' in log:
        return "🔴 You need to use Java 8 to play Forge on this version. Use this guide to install it, but make sure to install Java **8** instead: <https://docs.google.com/document/d/1aPF1lyBAfPWyeHIH80F8JJw8rvvy6lRm0WJ2xxSrRh8/edit#heading=h.62ygxgaxcs5a>."

def m1_failed_to_find_service_port(log):
    if 'java.lang.IllegalStateException: GLFW error before init: [0x10008]Cocoa: Failed to find service port for display' in log:
        return "🔴 You seem to be using an Apple M1 Mac with an incompatible version of Forge. Add the following to your launch arguments as a workaround: `-Dfml.earlyprogresswindow=false`"

def pixel_format_not_accelerated_win10(log):
    if 'org.lwjgl.LWJGLException: Pixel format not accelerated' in log:
        return "🔴 You seem to be using an Intel GPU that is not supported on Windows 10. You will need to install an older version of Java, see here for help: <https://github.com/MultiMC/MultiMC5/wiki/Unsupported-Intel-GPUs>."

def shadermod_optifine_conflict(log):
    if 'java.lang.RuntimeException: Shaders Mod detected. Please remove it, OptiFine has built-in support for shaders.' in log:
        return "🔴 You've installed a Shaders Mod alongside OptiFine. OptiFine has built-in shader support, so you should remove Shaders Mod."

def using_system_glfw(log):
    if 'Using system GLFW' in log:
        return "🟠 You seem to be using your system's GLFW installation. This can cause the instance to crash if not properly setup. In case of a crash, make sure this isn't the cause of it."

def using_system_openal(log):
    if 'Using system OpenAL' in log:
        return "🟠 You seem to be using your system's OpenAL installation. This can cause the instance to crash if not properly setup. In case of a crash, make sure this isn't the cause of it."

def sodium_config(log):
    if 'me.jellysquid.mods.sodium.client' in log:
        return '🔴 If your game crashes when you open the video settings menu or load into a world, delete `.minecraft/config/sodium-options.json`.'

def using_ssrng(mods,is_multimc_or_fork):
    if any("serverSideRNG" in mod for mod in mods):
        return f"🟡 You are using serverSideRNG. Currently the server for it is down, so the mod is useless and it's recommended to {'disable' if is_multimc_or_fork else 'delete'} it."

def random_log_spam_maskers(log):
    if ('Using missing texture, unable to load' in log
    or 'Exception loading blockstate definition' in log
    or 'Unable to load model' in log
    or 'java.lang.NullPointerException: Cannot invoke "com.mojang.authlib.minecraft.MinecraftProfileTexture.getHash()" because "?" is null' in log):
        return "🟡 Your log seems to have a lot of lines with random spam. It shouldn't cause any problems, and it's unknown what causes it. As far as we know, so far it has only happened to <@695658634436411404>."

def need_fapi(log):
    if 'requires any version of fabric, which is missing!' in log:
        return "🔴 You're using a mod that requires Fabric API. It is a mod that is separate to Fabric loader. You can download it here: <https://modrinth.com/mod/fabric-api>."

def dont_need_fapi(mods,mods_type):
    if mods_type == 3 and any('fabric-api' in mod for mod in mods):
        return "🟠 Note that you're using Fabric API, which is not allowed for speedrunning."

def couldnt_extract_native_jar(log):
    if "Couldn't extract native jar" in log:
        return '🔴 Another process appears to be locking your native library JARs. To solve this, please reboot your PC.'

def need_to_launch_as_admin(log):
    # happened in rankedcord: https://discord.com/channels/1056779246728658984/1074385256070791269/1118915678834020372
    pattern = re.compile(r'java\.io\.IOException: Directory \'(.+?)\' could not be created')
    if pattern.search(log):
        return '🟠 Try opening the launcher as administrator.'

def maskers_crash(log):
    if ('java.lang.RuntimeException: We are asking a region for a chunk out of bound' in log
    and 'Encountered an unexpected exception' in log
    and 'net.minecraft.class_148: Feature placement' in log
    and 'net.minecraft.server.MinecraftServer.method_3813(MinecraftServer.java:876)' in log
    and 'at net.minecraft.server.MinecraftServer.method_3748(MinecraftServer.java:813)' in log):
        return "🟢 This seems to be a rare crash that you can't do anything about. (https://discord.com/channels/928728732376649768/940285426441281546/1107588481556946998 from devcord)"

def lithium_crash(log):
    if ('java.lang.IllegalStateException: Adding Entity listener a second tim' in log
    and 'me.jellysquid.mods.lithium.common.entity.tracker.nearby' in log):
        return "🟢 This seems to be a rare crash caused by Lithium that you can't do anything about. It happens really rarely, so it's not worth it to stop using Lithium because of it."

def old_arr(mods):
    if 'antiresourcereload-1.16.1-1.0.0.jar' in mods:
        return "🔴 You're using an old version of AntiResourceReload, which can cause Minecraft to crash when entering practice maps. You should update it: <https://github.com/Minecraft-Java-Edition-Speedrunning/mcsr-antiresourcereload-1.16.1/releases/tag/latest>"

def parse_log(link):
    log = download_from_paste_ee_or_mclogs(link)
    if log is None:
        return None
    mods = get_mods_from_log(log)
    mods_type = get_mods_type(mods)
    java_version = get_java_version(log)
    major_java_version = get_major_java_version(java_version)
    minecraft_folder = get_minecraft_folder(log)
    OS = get_OS(minecraft_folder)
    minecraft_version = get_minecraft_version(log)
    fabric_loader_version = extract_fabric_loader_version(log)
    launcher = get_launcher(log)
    is_multimc_or_fork = get_is_multimc_or_fork(launcher)
    modloader = get_modloader(log)
    java_arguments = get_java_arguments(log)
    max_memory_allocation = get_max_memory_allocation(log)
    issues = [
        not_using_fabric(modloader, mods_type),
        should_use_prism(launcher, OS),
        need_java_17_plus(log, mods, major_java_version),
        using_32bit_java(log),
        outdated_srigt_fabric_01415(mods, fabric_loader_version, minecraft_version),
        outdated_fabric_loader(fabric_loader_version,mods),
        not_enough_ram_or_rong_sodium(max_memory_allocation, OS, mods, log, java_arguments),
        onedrive(minecraft_folder,launcher),
        hs_err_pid(log, mods),
        using_phosphor(mods, minecraft_version),
        failed_to_download_assets(log),
        id_range_exceeded(log),
        multimc_in_program_files(minecraft_folder),
        macos_too_new_java(log),
        forge_too_new_java(log),
        m1_failed_to_find_service_port(log),
        pixel_format_not_accelerated_win10(log),
        shadermod_optifine_conflict(log),
        using_system_glfw(log),
        using_system_openal(log),
        sodium_config(log),
        using_ssrng(mods,is_multimc_or_fork),
        random_log_spam_maskers(log),
        need_fapi(log),
        dont_need_fapi(mods,mods_type),
        couldnt_extract_native_jar(log),
        need_to_launch_as_admin(log),
        maskers_crash(log),
        lithium_crash(log),
        old_arr(mods)
    ]
    result = []
    for issue in issues:
        if issue:
            result.append(issue)
    return result





