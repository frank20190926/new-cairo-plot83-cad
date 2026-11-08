# Plot 83 / 参数化工程包说明

状态：**约束研究方案，不能宣称 100% 工程合规、不能施工或作为通过审批的设计。**

## 重建

```sh
python3 build_cad_2800443.py
python3 build_cad_2800443.py --write-default-config parameters.json
python3 build_cad_2800443.py --config parameters.json
```

只用现有 Python 环境的 `ezdxf` 和 `PyMuPDF`，未安装依赖、未修改用户配置。参数以米输入，DXF 以毫米、R2010 输出，图层包括指定的八层。PDF 为 A3 横向矢量页；SVG 字体转路径，无位图、无网络字体。两张 HTML 自包含，固定 1600×1200。

`Parameters` 集中定义地块、面积比例、楼层深度、退距、标高、坡道、车位、泳池、房间面积及日照纬度。导出共用几何原语，目标房间面积、泳池间距、边界包含关系自动检查。参数可变不等于任意取值都有建筑可行解：不成立的几何输入会触发断言，工程约束始终单独报告。

## 来源与边界

原始 JSON 的标题把方位写得含混；附图明确 P4-P1=17m、P1-P2=25m，按用户本轮的明确方向建模。附图确认 Plot 83、Sector B、西侧 84、南侧 10，未包含地勘、消防、结构和设备设计数据。纬度 30.03°N 为新开罗区域近似假定，并非测量坐标。N/NW 风向来自设计 brief，未伪造实测风玫瑰频率。

原始雇主 brief 写明 **AI-generated results are not accepted**。本包为 AI 辅助本地研究，未提交平台，不应隐瞒来源后参赛。

## 已核实尺寸

- 地块 17.00 × 25.00 = 425.00 m²；对角线 30.232433 m，显示 30.23m 为四舍五入。
- 首层 12.50 × 17.00 = 212.50 m²；标准层 13.75 × 17.00 = 233.75 m²；屋顶 10.625 × 10.00 = 106.25 m²。
- 面积为封闭外轮廓总面积；楼板悬挑、屋顶棚架计容方式未取得当地主管部门认可。地下室面积不套用地上50%比例。
- 泳池净水面 3×6m，外壳厚0.20m；1.50m从地下室外墙外表面量至泳池外壳外表面。南侧外壳仍在地块内。
- 六个车位按2.40×4.60m紧凑车型预留，示例车辆1.80×4.30m；不是一般大型轿车/SUV通用车库认证。6m标注为车位之间的净通道。

## 未消解的工程问题

### H01 / RAMP WIDTH / SETBACK

3.50 m clear ramp exceeds 3.00 m west setback; wall thickness additional.

A setback is not necessarily a ramp-width limit. The extra 0.50 m is reserved inside the plot, but permissibility and clearances below the typical-floor overhang are not established.

### H02 / RAMP CONNECTION / SWEPT PATH

21.333 m at 15% leaves 3.667 m; landing and 5.80 m outer turn do not fit.

The drawn straight ramp reaches basement datum behind the basement wall. Transition ramps, vehicle underside clearance, protected pedestrian path, road entry and connection to the parking aisle remain unresolved. Annular arcs do not validate six individual maneuvers.

### H03 / POOL OVERLOOK / EARTH BUFFER

A grade-height earth buffer obstructs basement full-height glazing and a seated pool view.

Pool shell is separate and the 1.50 m plan separation is exact. A lowered retained courtyard or revised pool level is required; either changes the requested arrangement. The section explicitly shows the conflict rather than hiding it.

### H04 / CORE PERFORMANCE CLAIM

Option B selected; the requested 14% net-to-gross advantage is not demonstrated.

Same-scale conceptual reservations: A 6.00 x 6.20 m, B 4.85 x 5.65 m. Core-excluded gross is only a proxy, not measured apartment net area. Stair, lift, fire strategy and structure need local design review.

### H05 / CODE / STRUCTURE / SERVICES

No structural, Egyptian-code, fire, accessibility, mechanical or local-authority certification.

Areas are gross horizontal rectangles. Roof pergola counting, cantilever permissions, perimeter spans, shaft continuity, room access and basement egress are schematic. Zero-waste and energy savings are strategies without measured performance claims.

### H06 / CONTEST ELIGIBILITY

Employer brief states: AI-generated results are not accepted. No submission performed.

This package is AI-assisted engineering concept work. Do not represent it as human-only authored or conceal its origin. The source title is ambiguous on orientation; attached plot image and user dimensions govern this study.

## 扫掠与核心筒计算

青色 Ri=3.2m、琥珀色 Ro=5.8m 是给定的内外包络半径模板；红色为坡道出口所需外转弯与场地的冲突。未将圆弧当作轴距、转向角、前后悬和逆车策略完整定义的车辆运动学验证。六个车位均已画出，但六条可达、可退出的真实路线未成立。

A 核心筒预留 6×6.2=37.20m²，B 预留4.85×5.65=27.4025m²，同一233.75m²标准层作分母。只可计算扣核心筒后的总面积比例，不能当实际套内净面积。楼梯图为20级/层、每级165mm及300mm踏步的标准层概念；地下室至首层3.65m需要单独校核踏步和净空。B 的规则剪力墙布局是概念，不是承载力或抗震验算结论。

## 输出与验证

- `engineering_validation.json`：参数、目标面积、实际矩形房间面积、DXF审计、未通过项。
- `requirement_matrix.md`：用户全部主要要求与实现/未验证状态。
- `manifest.json`：各图纸SHA-256与文件大小。
- ZIP包含本次DXF、完整PDF和所有SVG，另附报告，防止脱离说明后误用。
- `99_临时/qa/`：展板截图、PDF缩略图、浏览器布局检查。

不提交、不推送、不部署，不改全局规则与配置。
