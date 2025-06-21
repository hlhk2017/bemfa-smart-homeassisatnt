

# 巴法智能 Home Assistant 集成 (Bemfa Smart Home Assistant Integration)
## 巴法云 反向接入homeassistant
这是一个为 Home Assistant 设计的自定义集成，用于连接和控制巴法智能设备。它允许您将巴法智能平台上的设备（如灯光、空调、风扇、窗帘、传感器和各类开关）集成到 Home Assistant 中，并通过 Home Assistant 的界面进行控制和自动化。

## 特性 (Features)

* **设备支持**:
    * **灯光 (Light)**: 开/关控制.
    * **空调 (Climate)**: 开/关、模式（自动、制冷、制热、送风、除湿）、目标温度、风速（低、中、高）控制，并可在配置中关联外部温度传感器作为当前温度显示.
    * **风扇 (Fan)**: 开/关、多档速度控制（1-5档可配置）、摇头控制.
    * **窗帘 (Cover)**: 开/关、停止、设置具体位置（百分比）.
    * **传感器 (Sensor)**: 温度、湿度等数据显示.
    * **开关 (Switch)**:
        * **通用开关**: 支持巴法智能中 `id` 为 `switch` 的设备，显示通用开关图标.
        * **智能插座**: 支持巴法智能中 `id` 为 `outlet` 的设备，显示插座图标.
        * **空调开关**: 为空调设备提供独立的开关实体，可方便地控制空调的整体开关状态.
* **数据刷新**: 通过设置扫描间隔，定期从巴法智能云平台获取设备最新状态.
* **配置流程**: 提供 Home Assistant 标准的配置流程 (Config Flow) 进行设置，无需手动编辑 YAML 文件.
* **外部传感器关联**: 支持通过 Home Assistant UI 为空调设备灵活关联已有的温度传感器，使其显示真实环境温度.
* **风扇挡位数配置**: 支持通过 Home Assistant UI 为每个风扇单独配置其支持的最大挡位数（1-5档），以适应不同型号风扇的需求.

## 安装 (Installation)

目前，此集成是一个自定义组件。您可以通过以下两种方式安装：

### 1. 通过 HACS (推荐) (Via HACS - Recommended)

1.  确保您已安装 [HACS (Home Assistant Community Store)](https://hacs.xyz/)。
2.  在 Home Assistant 侧边栏中进入 **HACS**。
3.  点击右下角的 **`+`** 按钮，选择 **“自定义存储库 (Custom Repositories)”**。
4.  在弹出的对话框中：
    * **存储库 (Repository)** 填写此集成的 GitHub 仓库地址（例如：`https://github.com/hlhk2017/bemfa-smart-homeassisatnt`）.
    * **类别 (Category)** 选择 `集成 (Integration)`。
5.  点击 **“添加 (Add)”**。
6.  HACS 将会找到该集成，然后点击 **“安装 (Install)”**。
7.  安装完成后，**重启 Home Assistant**。

### 2. 手动安装 (Manual Installation)

1.  在您的 Home Assistant 配置文件夹 (`config` 文件夹) 中，创建一个名为 `custom_components` 的文件夹（如果它不存在）。
2.  将此集成仓库中的所有文件（即 `bemfa_smart` 文件夹及其所有内容）复制到 `custom_components` 文件夹内。
    例如，路径将是：`<config_dir>/custom_components/bemfa_smart/`。
3.  **重启 Home Assistant**。

## 配置 (Configuration)

安装并重启 Home Assistant 后，您可以通过 UI 进行配置。

1.  进入 Home Assistant 的 **“设置 (Settings)”** -> **“设备与服务 (Devices & Services)”**。
2.  点击右下角的 **“添加集成 (Add Integration)”** 按钮。
3.  搜索 **“巴法智能 (Bemfa Smart)”** 并选择它。
4.  根据提示输入您的巴法智能 **用户ID (User ID)**.
5.  您还可以配置 **扫描间隔 (Scan Interval)**，默认是 30 秒，范围为 1 到 60 秒.
6.  点击 **“提交 (Submit)”** 完成初始配置。
7. userid的获取： 打开巴法云网页，f12调出开发者模式。然后如下图：

![87547fd6e4b6c088656ea5c508b2c34](https://github.com/user-attachments/assets/c3f2b107-d4b5-49cd-8970-214322caddea)

集成成功添加后，您的巴法智能设备将自动出现在 Home Assistant 中。

### 选项配置 (Options Configuration)

您可以在集成设置中管理全局选项以及特定设备的配置：

1.  进入 **“设置 (Settings)”** -> **“设备与服务 (Devices & Services)”**。
2.  找到已配置的 **“巴法智能 (Bemfa Smart)”** 集成卡片，点击 **“配置 (Configure)”** 按钮。
3.  您将看到一个主菜单，可以选择以下操作：
    * **全局设置 (Global Settings)**: 调整 **“数据扫描间隔 (Scan Interval)”**.
    * **配置空调温度传感器 (Configure AC Temperature Sensors)**: 进入子菜单，为每个空调设备选择一个 Home Assistant 中已有的温度传感器实体。配置完成后，您可以选择继续配置其他空调或返回主菜单.
    * **配置风扇挡位数量 (Configure Fan Speed Levels)**: 进入子菜单，为每个风扇设备单独设置其支持的最大挡位数（1-5档）。配置完成后，您可以选择继续配置其他风扇或返回主菜单.
    * **完成并保存配置 (Finish and Save Configuration)**: 保存所有修改并退出配置流程。

## 支持的 Home Assistant 版本 (Supported Home Assistant Versions)

此集成支持 Home Assistant 版本 `2025.4.2+`.

## 故障排除 (Troubleshooting)

如果您遇到问题，请检查以下几点：

1.  **用户ID是否正确？** 确保您输入的巴法智能用户ID是正确的.
2.  **网络连接？** 确认您的 Home Assistant 实例可以访问巴法智能的 API 地址 (`https://pro.bemfa.com`).
3.  **Home Assistant 日志？** 检查 Home Assistant 的日志 (`config/home-assistant.log`)，搜索 `bemfa_smart` 或 `ERROR` 关键字，可能会有详细的错误信息。
4.  **设备ID/类型？** 确保您的巴法智能设备在平台上注册的类型与集成代码中支持的类型匹配 (`light`, `aircondition`, `fan`, `curtain`, `sensor`, `outlet`, `switch`).
5.  **设备数据是否更新？** 如果设备状态没有及时更新，请检查扫描间隔设置是否过长，或者巴法智能平台上的设备状态是否正常。

## 开发 (Development)

项目地址：[https://github.com/hlhk2017/bemfa-smart-homeassisatnt](https://github.com/hlhk2017/bemfa-smart-homeassisatnt)

如果您是开发者并希望贡献代码，请通过 GitHub 提交通知 (Issues) 或拉取请求 (Pull Requests)。

## 许可证 (License)

此项目根据 MIT 许可证发布。

---

**注意**: 此自定义集成非巴法智能官方开发，而是由社区维护。
