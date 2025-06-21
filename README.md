# 巴法智能 Home Assistant 集成 (Bemfa Smart Home Assistant Integration)

这是一个为 Home Assistant 设计的自定义集成，用于连接和控制巴法智能设备。它允许您将巴法智能平台上的设备（如灯光、空调、风扇、窗帘和传感器）集成到 Home Assistant 中，并通过 Home Assistant 的界面进行控制和自动化。

## 特性 (Features)

* **设备支持**:
    * **灯光 (Light)**: 开/关控制.
    * **空调 (Climate)**: 开/关、模式（自动、制冷、制热、送风、除湿）、目标温度、风速（低、中、高）控制，并可集成外部温度传感器作为当前温度显示.
    * **风扇 (Fan)**: 开/关、三档速度控制（低、中、高）、摇头控制.
    * **窗帘 (Cover)**: 开/关、停止、设置具体位置（百分比）.
    * **传感器 (Sensor)**: 温度、湿度等数据显示.
    * **开关 (Switch)**: 空调设备的开关实体，可以单独控制空调的开关状态.
* **数据刷新**: 通过设置扫描间隔，定期从巴法智能云平台获取设备最新状态.
* **配置流程**: 提供 Home Assistant 标准的配置流程 (Config Flow) 进行设置，无需手动编辑 YAML 文件.

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
5.  您还可以选择配置 **扫描间隔 (Scan Interval)**，默认是 30 秒，范围为 1 到 60 秒.
6.  点击 **“提交 (Submit)”** 完成配置。

集成成功添加后，您的巴法智能设备将自动出现在 Home Assistant 中。

### 选项配置 (Options Configuration)

您可以在集成设置中修改扫描间隔：

1.  进入 **“设置 (Settings)”** -> **“设备与服务 (Devices & Services)”**。
2.  找到已配置的 **“巴法智能 (Bemfa Smart)”** 集成卡片，点击 **“配置 (Configure)”** 按钮。
3.  您可以调整 **“扫描间隔 (Scan Interval)”**.
4.  点击 **“提交 (Submit)”** 保存更改。

## 支持的 Home Assistant 版本 (Supported Home Assistant Versions)

此集成支持 Home Assistant 版本 `2025.4.2+`.

## 故障排除 (Troubleshooting)

如果您遇到问题，请检查以下几点：

1.  **用户ID是否正确？** 确保您输入的巴法智能用户ID是正确的。
2.  **网络连接？** 确认您的 Home Assistant 实例可以访问巴法智能的 API 地址 (`https://pro.bemfa.com`).
3.  **Home Assistant 日志？** 检查 Home Assistant 的日志 (`config/home-assistant.log`)，搜索 `bemfa_smart` 或 `ERROR` 关键字，可能会有详细的错误信息。
4.  **设备ID/类型？** 确保您的巴法智能设备在平台上注册的类型与集成代码中支持的类型匹配.
5.  **设备数据是否更新？** 如果设备状态没有及时更新，请检查扫描间隔设置是否过长，或者巴法智能平台上的设备状态是否正常。

## 开发 (Development)

项目地址：[https://github.com/hlhk2017/bemfa-smart-homeassisatnt](https://github.com/hlhk2017/bemfa-smart-homeassisatnt)

如果您是开发者并希望贡献代码，请通过 GitHub 提交通知 (Issues) 或拉取请求 (Pull Requests)。

## 许可证 (License)

此项目根据 MIT 许可证发布。

---

**注意**: 此自定义集成非巴法智能官方开发，而是由社区维护。
