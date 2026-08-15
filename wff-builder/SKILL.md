# WFF Builder Skill

Build Watch Face Format (WFF) APKs for Wear OS. Pure Python pipeline, no Android Studio required.

## When to Use

- Build a WFF watch face APK
- Validate watchface.xml against known rules
- Initialize a new WFF project

## Quick Start

```bash
# Initialize new project
python /home/z/my-project/experiments/wff-builder/wff_builder.py init projects/my_watch

# Edit these 3 files:
#   projects/my_watch/project.yaml    — package name, version
#   projects/my_watch/watchface.xml   — WFF XML design
#   projects/my_watch/preview.png     — 384x384 preview image

# Validate (check rules before build)
python wff_builder.py validate projects/my_watch

# Build APK
python wff_builder.py build projects/my_watch
```

## Project Structure (developer provides 3 files)

```
projects/my_watch/
├── project.yaml     # REQUIRED: package config
├── watchface.xml    # REQUIRED: WFF design
├── preview.png      # REQUIRED: 384x384 preview
├── background.png   # OPTIONAL: extra drawables
└── custom.ttf       # OPTIONAL: extra fonts
```

## project.yaml Format

```yaml
package_name: com.example.mywatchface
version_code: 1
version_name: "1.0"
watch_face_name: My Watch Face
wff_version: 1              # 1=Wear OS 4 (minSdk 33), 2+=Wear OS 5+ (minSdk 34)
```

## WFF XML Rules (16 rules, auto-validated)

### MUST (error = build fails)

| ID | Rule | Bad | Good |
|----|------|-----|------|
| R01 | WatchFace root must have width+height | `<WatchFace>` | `<WatchFace width="450" height="450">` |
| R02 | Must have Metadata CLOCK_TYPE | (missing) | `<Metadata key="CLOCK_TYPE" value="DIGITAL"/>` |
| R03 | Must have Metadata PREVIEW_TIME | (missing) | `<Metadata key="PREVIEW_TIME" value="10:08:32"/>` |
| R05 | Data source expressions MUST use square brackets | `expression="MONTH"` | `expression="[MONTH]"` |
| R06 | No clipShape (WFF v1 unsupported) | `clipShape="CIRCLE"` | (remove it) |
| R08 | Colors must be 8-digit ARGB | `color="#00F5FF"` | `color="#ff00F5FF"` |
| R09 | Time uses DigitalClock+TimeText, not Text+Template | `<Text>..%s..` | `<DigitalClock><TimeText format="HH:mm">` |
| R11 | Use expression= not source= | `source="MONTH"` | `expression="[MONTH]"` |
| R12 | Parameter must use expression= | `<Parameter source="X"/>` | `<Parameter expression="[X]"/>` |
| R14 | %s count must match Parameter count in Template | 2 `%s` + 1 Parameter | match them |
| R16 | No WatchFaceService declarations | `<service>` | (remove) |

### SHOULD (warn = build continues)

| ID | Rule | Fix |
|----|------|-----|
| R04 | Scene should have backgroundColor | `backgroundColor="#ff000000"` |
| R07 | Font family should be SYNC_TO_DEVICE | `family="SYNC_TO_DEVICE"` |
| R10 | Should have ambient Variant | `<Variant mode="AMBIENT" target="alpha" value="0"/>` |
| R13 | Use known data source names | see list below |
| R15 | Digital time prefers DigitalClock | use `<DigitalClock><TimeText>` |

## Valid WFF Data Sources

```
Time:    [HOUR_0_23] [HOUR_1_12] [HOUR_Z] [MINUTE_Z] [SECOND_Z]
         [SECONDS_IN_DAY] [AMPM_STATE] [AMPM_STRING]
Date:    [DAY] [DAY_Z] [DAY_0_30] [DAY_OF_WEEK_S] [DAY_OF_WEEK]
         [DAYS_IN_MONTH] [MONTH] [MONTH_S] [YEAR]
Battery: [BATTERY_PERCENT]
Heart:   [HEART_RATE]
Config:  [CONFIGURATION.<id>]
Comp:    [COMPLICATION.TEXT] [COMPLICATION.TITLE] [COMPLICATION.MONOCHROMATIC_IMAGE]
Weather: [WEATHER.TEMPERATURE] [WEATHER.IS_DAY] [WEATHER.CONDITION] ...
```

## Correct watchface.xml Skeleton

```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
    <Metadata key="PREVIEW_TIME" value="10:08:32"/>
    <Scene backgroundColor="#ff000000">
        <DigitalClock x="0" y="0" width="450" height="450">
            <!-- Active mode (bright) -->
            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="150" width="450" height="120" alpha="255">
                <Variant mode="AMBIENT" target="alpha" value="0"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>
            </TimeText>
            <!-- Ambient mode (dim) -->
            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"
                      align="CENTER" x="0" y="150" width="450" height="120" alpha="0">
                <Variant mode="AMBIENT" target="alpha" value="255"/>
                <Font family="SYNC_TO_DEVICE" size="100" weight="THIN" color="#ff888888"/>
            </TimeText>
        </DigitalClock>

        <!-- Date -->
        <PartText x="0" y="260" width="450" height="50">
            <Variant mode="AMBIENT" target="alpha" value="0"/>
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="32" weight="NORMAL" color="#ffAAAAAA">
                    <Template>%s/%s
                        <Parameter expression="[MONTH]"/>
                        <Parameter expression="[DAY]"/>
                    </Template>
                </Font>
            </Text>
        </PartText>
    </Scene>
</WatchFace>
```

## Build Pipeline (automated)

1. **Validate** watchface.xml against 16 rules
2. **Generate** AndroidManifest.xml, watch_face_info.xml, strings.xml
3. **Compile** with aapt2 → binary AXML + resources.arsc
4. **Extract** compiled resources from template APK
5. **Package** ZIP with resources.arsc STORED + 4-byte aligned
6. **Sign** with apksigner

## Critical Build Constraints

- `res/xml/` files MUST be binary AXML (extracted from aapt2 output, NOT raw text)
- `res/raw/` files stay as raw text (NOT compiled)
- `resources.arsc` MUST be STORED (uncompressed) + 4-byte aligned
- `res/values/` MUST NOT appear in final APK (compiled into resources.arsc)
- WFF v1 → minSdk 33, WFF v2+ → minSdk 34

## Install

```bash
# Same signature: just reinstall
adb install -r my-watchface.apk

# Different signature: uninstall first
adb uninstall com.example.mywatchface && adb install my-watchface.apk
```

## Environment

- ANDROID_HOME: /home/z/my-project/tools/android-sdk
- Build-Tools: 34.0.0 (x86_64 only, Docker required on ARM64)
- Keystore: /home/z/my-project/experiments/wff-apk-test/test.keystore (pass: wfftest123)
