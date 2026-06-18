# Relay Control Plugin (RQT)

## Overview

The **Relay Control Plugin** is an RQT plugin for ROS1 designed to easily send control commands (`on`, `off`, `toggle`) to relay hardware modules via `std_msgs/String` topics.

It automatically inspects the global ROS Master graph to discover all existing topics with matching message types, filtering out inactive or unrelated channels.

**Works perfectly with our [relay control package](https://github.com/CJT-Robotics/relay_control.git)**

## Requirements

Install the required ROS packages:

```bash
sudo apt install ros-noetic-rqt ros-noetic-rqt-common-plugins
```

## Installation

Clone the repository into your Catkin workspace:

```bash
cd ~/catkin_ws/src
git clone git@github.com:CJT-Robotics/relay_control_plugin.git
```

Build the workspace:

```bash
cd ~/catkin_ws
catkin_make
```

Source the workspace:

```bash
source devel/setup.bash
```

## Usage
Launch RQT on the operator station:

```bash
rqt --force-discover
```

> After the first successful run, `--force-discover` is usually no longer necessary.

Load the plugin:

```text
Plugins → CJT-Robotics → Relay Control Panel
```

---

## Features

#### Persistent Settings

The plugin remembers the last selected topic across RQT restarts using the built-in RQT settings infrastructure.

## Troubleshooting