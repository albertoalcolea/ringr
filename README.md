# ringr

[![Build Status](https://github.com/albertoalcolea/ringr/workflows/Tests/badge.svg)](https://github.com/albertoalcolea/ringr/actions?query=workflow%3ATests)
[![Latest PyPI Version](https://img.shields.io/pypi/v/ringr.svg)](https://pypi.python.org/pypi/ringr)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/ringr.svg)](https://pypi.python.org/pypi/ringr)

Sound event detection system based on the open-source cross-platform PortAudio API.

It supports multiple notification backends, and it has been designed to run on low-specs and inexpensive hardware like the lowest range of raspberry products (RPi 1, RPi Zero, RPi Zero 2, etc).

## Use cases

Some interesting use cases where to use *ringr* to automate your smart home and help disabled people:
* Intercom and doorbell detection
* Detection of the end-of-program audible warning of some appliances such as washing machines, clothes dryers or dishwashers
* Baby crying detection
* Dog bark detection

## Design considerations and constraints

This has born as a personal project for a very concrete use case that can be extrapolated to multiple other contexts and needs.

Some of my personal requirements and constraints include:
* It must run on an old Raspberry Pi 1 that I have stored in a drawer and unused for some many years to give it a new life.
* It must run with very cheap and low quality microphones.
* It must be able to detect the intercom and doorbell notification sounds without false positives warnings.
* It must notify states to my personal Home Assistant installation and provide support to add more notification backends in the future.

More information about the concept and design of *ringr* in [this post on my personal blog](https://albertoalcolea.com/blog/ringr-a-sound-event-detection-system/).

## Installation

On all systems, install *ringr* by using `pip`:

```
pip install ringr
```

If you install *ringr* on macOS and Windows, the PortAudio library will be installed automatically. On other platforms, you might have to install PortAudio with your package manager (the package might be called `libportaudio2` or similar).

### Systemd

Copy the file `ringr.service` available in this repository to `/etc/systemd/system/ringr.service`

Edit the service and modify the application path, the user and the group if needed.

Reload the systemd daemon to load the new service by executing `systemctl daemon-reload`.

Start the service with `systemctl start ringr.service` and enable it if you want to run it automatically at startup: `systemctl enable ringr.service`

### Docker

Alternatively to a native installation you can use Docker.

A Dockerfile is provided to build a Docker image for *ringr*.

```
docker build -t ringr .
```

No volumes are needed as *ringr* is a stateless service.

Remember you need to add the host sound device to your container with `--device`

```
docker run -d \
  --name=ringr \
  --device=/dev/snd:/dev/snd
  -e TZ=Europe/Madrid \
  -e PUID=1000 \
  -e GUID=1000 \
  -e RINGR_DETECTOR_DEVICE='1' \
  -e RINGR_DETECTOR_THRESHOLD='65' \
  -e RINGR_DETECTOR_PEAK_DURATION='0.8' \
  -e RINGR_DETECTOR_FREQUENCY='1000' \
  -e RINGR_DETECTOR_ACCEPTANCE_RATIO='90' \
  -e RINGR_DETECTOR_GAIN='200' \
  -e RINGR_DETECTOR_LATENCY='0.1' \
  -e RINGR_DETECTOR_COOLDOWN='15' \
  -e RINGR_NOTIFIER_TYPE='ha' \
  -e RINGR_NOTIFIER_MQTT_HOST='10.10.0.50' \
  -e RINGR_NOTIFIER_USER='ringr' \
  -e RINGR_NOTIFIER_PASS='secret' \
  --restart unless-stopped \
  ringr:latest
```

#### docker-compose

Example of a *docker-compose* file:

```
version: '3'
services:
  ringr:
    container_name: ringr
    image: ringr:latest
    devices:
      - '/dev/snd:/dev/snd'
    environment:
      TZ: 'Europe/Madrid'
      PUID: '1000'
      GUID: '1000'
      RINGR_DETECTOR_DEVICE: '1'
      RINGR_DETECTOR_THRESHOLD: '65'
      RINGR_DETECTOR_PEAK_DURATION: '0.8'
      RINGR_DETECTOR_FREQUENCY: '1000'
      RINGR_DETECTOR_ACCEPTANCE_RATIO: '90'
      RINGR_DETECTOR_GAIN: '200'
      RINGR_DETECTOR_LATENCY: '0.1'
      RINGR_DETECTOR_COOLDOWN: '15'
      RINGR_NOTIFIER_TYPE: 'ha'
      RINGR_NOTIFIER_MQTT_HOST: '10.10.0.50'
      RINGR_NOTIFIER_USER: 'ringr'
      RINGR_NOTIFIER_PASS: 'secret'
    restart: unless-stopped
```

## Usage

Use the `ringr` command to launch the application.

It supports the following optional parameters:
* `-c`, `--conf`: configuration file. By default it uses `/etc/ringr/ringr.conf`
* `-v`, `--verbose`: configure the log level of the logger in debug level

## Configuration

*ringr* can be configured through a configuration file or with environment variables, useful if you run it  within a docker container.

The expected path to the configuration file is `/etc/ringr/ringr.conf`.

### Detector

The configuration of the detector is defined inside the `[detector]` section of the configuration files.

It supports the following options:

#### device

| Option | Environment variable | Data type | Unit | Default |
| --- | --- | --- | --- | --- |
| `device` | `RINGR_DETECTOR_DEVICE` | integer | | |

Index of the input sound device.

You can get the list of PortAudio sound devices and their index with the following command:

```
$ python -m sounddevice
  0 sof-hda-dsp: - (hw:1,0), ALSA (2 in, 2 out)
  1 sof-hda-dsp: - (hw:1,4), ALSA (0 in, 2 out)
  2 sof-hda-dsp: - (hw:1,5), ALSA (0 in, 2 out)
  3 sof-hda-dsp: - (hw:1,6), ALSA (2 in, 0 out)
  4 sof-hda-dsp: - (hw:1,7), ALSA (2 in, 0 out)
  5 pulse, ALSA (32 in, 32 out)
* 6 default, ALSA (32 in, 32 out)
```

#### threshold

| Option | Environment variable | Data type | Unit | Default |
| --- | --- |-----------|------| --- |
| `threshold` | `RINGR_DETECTOR_THRESHOLD` | float     | %  | |

Relative amplitude threshold for the event detection.  It must be a value in the range [0,100].

#### peak_duration

| Option | Environment variable | Data type | Unit  | Default |
| --- | --- |-----------|-------| --- |
| `peak_duration` | `RINGR_DETECTOR_PEAK_DURATION` | float     | secs. | |

Duration of the signal over the threshold amplitude before to be considered an event.

#### frequency

| Option      | Environment variable       | Data type | Unit | Default |
|-------------|----------------------------|-----------|---| --- |
| `frequency` | `RINGR_DETECTOR_FREQUENCY` | int       | Hz | |

Frequency where to analyze the event.

The event will be analyzed inside a frequency range where the highest frequency will be the closest possible frequency to the desired frequency based on the number of frequency bins used.

#### frequency_bins

| Option           | Environment variable            | Data type | Unit | Default |
|------------------|---------------------------------|-----------|-|---------|
| `frequency_bins` | `RINGR_DETECTOR_FREQUENCY_BINS` | int       | | 256     |

Number of frequency bins in which divide the range of audible frequencies.

The detector will analyze the frequency bin whose highest frequency is closest to the desired frequency.

For example, with `frequency = 1000` and `frequency_bins` = 256, the detector will analyze the range between 951 Hz and 1037 Hz.

#### acceptance_ratio

| Option           | Environment variable              | Data type | Unit | Default |
|------------------|-----------------------------------|-----------|------|---------|
| `acceptance_ratio` | `RINGR_DETECTOR_ACCEPTANCE_RATIO` | float     | %    | 100     |

Number of samples that must be above the amplitude threshold in the desired frequency range during the `peak_duration` time.

#### gain

| Option | Environment variable  | Data type | Unit | Default |
|--------|-----------------------|-----------|------|--------|
| `gain` | `RINGR_DETECTOR_GAIN` | int       |     | 0     |

Some input devices may capture very low signals. Use this parameter to boost them to have more control on its amplitude.

#### latency

| Option    | Environment variable     | Data type | Unit  | Default |
|-----------|--------------------------|-----------|-------|---------|
| `latency` | `RINGR_DETECTOR_LATENCY` | float     | secs. | *high*  |

Input latency of capture.

Higher values will prevent input overflow errors that will discard samples and produce more robust and predictable results.

By default, it will use the predefined high input latency of your input sound device.

You can query that value using the following command replacing the argument in the `query_devices` method by the device index of your device:

```
$ python -c 'import sounddevice as sd; print(sd.query_devices(1))'
{'name': 'default', 'index': 11, 'hostapi': 0, 'max_input_channels': 32, 'max_output_channels': 32, 'default_low_input_latency': 0.008684807256235827, 'default_low_output_latency': 0.008684807256235827, 'default_high_input_latency': 0.034807256235827665, 'default_high_output_latency': 0.034807256235827665, 'default_samplerate': 44100.0}
```

#### cooldown

| Option     | Environment variable      | Data type | Unit  | Default |
|------------|---------------------------|-----------|-------|---------|
| `cooldown` | `RINGR_DETECTOR_COOLDOWN` | float     | secs. | 10      |

Cooldown time in seconds after a detection.  Any sample during this period will be discarded and will not be analyzed.

#### block_duration

| Option    | Environment variable           | Data type | Unit       | Default |
|-----------|--------------------------------|-----------|------------|---------|
| `block_duration` | `RINGR_DETECTOR_BLOCK_DURATION` | float     | millisecs. | 50      |

Duration of the sample to analyze.

Higher values may provoke input overflow errors.

#### log_analysis

| Option         | Environment variable          | Data type | Unit       | Default |
|----------------|-------------------------------|-----------|------------|---------|
| `log_analysis` | `RINGR_DETECTOR_LOG_ANALYSIS` | bool      |  | False   |


Verbose output of analysis. Use with log level = debug

### Notification backends

The configuration of the chosen notification backend is defined inside the `[notifier]` section of the configuration file.

All notification backends share one option: `type` which specifies the notification backend to use. The corresponding environment variable for this option is `RINGR_NOTIFIER_TYPE`


Available notification backends:

| Name | Type | Description |
| --- | --- | --- |
| Home Assistant | `ha` | Auto-discoverable MQTT device for Home Assistant |
| Telegram | `telegram` | Telegram Bot |


#### Home Assistant

Use `type: ha`

| Option      | Environment variable         | Data type | Default    | Description                                                                                                             |
|-------------|------------------------------|-----------|------------|-------------------------------------------------------------------------------------------------------------------------|
| `device_id` | `RINGR_NOTIFIER_DEVICE_ID`   | str       | ringr_01   | Unique device id. Override this value if you run multiple instances of *ringr*                                          |
| `device_name` | `RINGR_NOTIFIER_DEVICE_NAME` | str       | ringr 01   | Device name. Override this value if you run multiple instances of *ringr* or to use a custom name within Home Assistant |
| `mqtt_host` | `RINGR_NOTIFIER_MQTT_HOST`   | str       |            | Host of the MQTT broker                                                                                                 |
| `mqtt_port` | `RINGR_NOTIFIER_MQTT_PORT`   | int       | 1883       | Port of the MQTT broker                                                                                                 |
| `mqtt_user` | `RINGR_NOTIFIER_MQTT_USER`   | str       |            | Optional username to authenticate with the MQTT broker. Use it together with `mqtt_pass`                                |
| `mqtt_pass` | `RINGR_NOTIFIER_MQTT_PASS`   | str       |            | Optional password to authenticate with the MQTT broker. Use it together with `mqtt_user`                                |
| `mqtt_client_id` | `RINGR_NOTIFIER_MQTT_CLIENT_ID` | str | `ringr_01` | Client id of the MQTT client. Override this value if you run multiple instances of *ringr*                              |
| `mqtt_qos` | `RINGR_NOTIFIER_MQTT_QOS` | int | 1          | MQTT QoS of published messages                                                                                          |

#### Telegram

Use `type: telegram`

| Option      | Environment variable         | Data type | Default    | Description |
|-------------|------------------------------|-----------|------------|---|
| `api_token` | `RINGR_NOTIFIER_API_TOKEN` | str | | Telegram Bot API Token |
| `chat_id` | `RINGR_NOTIFIER_CHAT_ID` | str | | Telegram Chat ID |
| `message` | `RINGR_NOTIFIER_MESSAGE` | str  | Event detected | Message to send where an event is detected |

### Full example

Configuration file:

```python
[detector]
device: 1
threshold: 65
peak_duration: 0.8
frequency: 1000
acceptance_ratio: 90
gain: 200
latency: 0.1
cooldown: 15

[notifier]
type: ha
mqtt_host: 10.10.0.50
mqtt_user: ringr
mqtt_pass: secret
```

Or, by using environment variables:

```bash
RINGR_DETECTOR_DEVICE='1'
RINGR_DETECTOR_THRESHOLD='65'
RINGR_DETECTOR_PEAK_DURATION='0.8'
RINGR_DETECTOR_FREQUENCY='1000'
RINGR_DETECTOR_ACCEPTANCE_RATIO='90'
RINGR_DETECTOR_GAIN='200'
RINGR_DETECTOR_LATENCY='0.1'
RINGR_DETECTOR_COOLDOWN='15'

RINGR_NOTIFIER_TYPE='ha'
RINGR_NOTIFIER_MQTT_HOST='10.10.0.50'
RINGR_NOTIFIER_USER='ringr'
RINGR_NOTIFIER_PASS='secret'
```
