# Consul Smart Beer - Home Assistant Integration

Custom Home Assistant integration for the **Consul Smart Beer** (cervejeira inteligente) using the Whirlpool Sixth Sense API.

## Features

- 🌡️ **Temperature Monitoring**: View current temperature setting
- 🎯 **Temperature Control**: Set target temperature (-4°C to 5°C)
- ❄️ **Turbo Mode**: Quick cooling control
- 🔒 **Display Lock**: Lock/unlock the physical display
- 📶 **Connectivity Status**: Monitor online/offline status

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL and select "Integration" as category
5. Click "Download"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/consul_smart_beer` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Consul Smart Beer"
4. Enter your Consul account credentials (same as the Consul Lar app)

## Entities

After configuration, the following entities will be created for each Smart Beer device:

### Sensors

- **Temperature**: Current temperature setting (°C)

### Binary Sensors

- **Online**: Device connectivity status

### Switches

- **Happy Hour**: Enable/disable rapid cooling
- **Display Lock**: Lock/unlock the physical controls

### Selects

- **Target Temperature**: Set the desired temperature with the following options:
  - -4°C (Mais gelado)
  - -2°C
  - 0°C
  - 3°C
  - 5°C (Menos gelado)

## Temperature Settings

The Smart Beer supports the following temperature presets:

| Setting | Temperature |
| ------- | ----------- |
| Coldest | -4°C        |
| Cold    | -2°C        |
| Medium  | 0°C         |
| Cool    | 3°C         |
| Warmest | 5°C         |

## Troubleshooting

### Authentication Issues

- Ensure you're using the same credentials as the Consul Lar app
- Try logging out and back into the Consul Lar app to verify your credentials

### Device Not Found

- Make sure your Smart Beer is set up and connected in the Consul Lar app
- The device must be online and connected to WiFi

### Connection Issues

- The integration uses Consul's cloud servers (same as the app)
- Check your internet connection
- Consul's servers may occasionally be unavailable

## Credits

This integration uses the [whirlpool-sixth-sense](https://github.com/abmantis/whirlpool-sixth-sense) library.

## License

MIT License
