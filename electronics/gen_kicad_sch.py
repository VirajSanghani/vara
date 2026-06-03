"""Generate openable KiCad-10 .kicad_sch for VARA core + cartridge.

Approach (within the kicad-cli ceiling — see tool-capabilities.md Addendum 2): kicad-cli
cannot place symbols, so we hand-author valid s-expression schematics. Connectivity is by
GLOBAL LABELS placed at each pin endpoint — global labels join by name across the sheet, so
positions are cosmetic and nets are exact. Each component gets a generated rectangular symbol
with its real pins. Two separate sheets (core, cartridge); the 6-pin pogo is the boundary
(J2 on core, PADS1 on cartridge), pin-labelled identically per connector-spec v0.2.

This is a DESIGN. Not DRC-clean, not manufactured, not electrically verified.
"""
import uuid, sys

G = 1.27  # KiCad connection grid (mm)
def u(): return str(uuid.uuid4())
def snap(v): return round(round(v / G) * G, 4)

# component = dict(ref, value, fp, desc, pins=[(number, name, net), ...])
CORE = [
    dict(ref="A1", value="RPi Zero 2 W", fp="", desc="Compute module (40-pin header + CSI)", pins=[
        ("2","5V","+5V"),("4","5V","+5V"),("6","GND","GND"),("9","GND","GND"),
        ("19","GPIO10_MOSI","SPI_MOSI"),("23","GPIO11_SCLK","SPI_SCLK"),("24","GPIO8_CE0","DISP_CS"),
        ("22","GPIO25","DISP_DC"),("18","GPIO24","DISP_RST"),("33","GPIO13_PWM1","DISP_BLK"),
        ("12","GPIO18_BCLK","I2S_BCLK"),("35","GPIO19_LRCLK","I2S_LRCLK"),
        ("38","GPIO20_PCMDIN","I2S_DIN"),("40","GPIO21_PCMDOUT","I2S_DOUT"),
        ("29","GPIO5","ENC_A"),("31","GPIO6","ENC_B"),("36","GPIO16","ENC_SW"),
        ("37","GPIO26","CART_VEN"),("3","GPIO2_SDA1","I2C_SDA"),("5","GPIO3_SCL1","I2C_SCL"),
        ("16","GPIO23","CART_CD"),("32","GPIO12","CART_INT"),("CSI","CAM_CSI","CSI")]),
    dict(ref="U2", value="IP5306", fp="Package_SO:ESOP-8", desc="PMIC: charge+boost+path+button", pins=[
        ("VIN","VIN","+VBUS"),("BAT","BAT","VBAT"),("VOUT","VOUT_5V","+5V"),("GND","GND","GND"),("KEY","KEY","ENC_SW")]),
    dict(ref="U6", value="AP2112K-3.3", fp="Package_TO_SOT_SMD:SOT-23-5", desc="3V3 LDO 600mA", pins=[
        ("1","VIN","+5V"),("2","GND","GND"),("3","EN","+5V"),("5","VOUT","+3V3_SYS")]),
    dict(ref="U5", value="TPS22918", fp="Package_TO_SOT_SMD:SOT-23-6", desc="Load switch (V+ to cartridge)", pins=[
        ("1","VIN","+3V3_SYS"),("2","GND","GND"),("3","ON","CART_VEN"),("4","VOUT","V+_SW")]),
    dict(ref="DS1", value="ST7789 1.69in 240x280", fp="", desc="SPI IPS display", pins=[
        ("VCC","VCC","+3V3_SYS"),("GND","GND","GND"),("SCL","SCL","SPI_SCLK"),("SDA","SDA","SPI_MOSI"),
        ("RES","RES","DISP_RST"),("DC","DC","DISP_DC"),("CS","CS","DISP_CS"),("BLK","BLK","DISP_BLK")]),
    dict(ref="MK1", value="SPH0645LM4H", fp="", desc="I2S MEMS mic", pins=[
        ("3V3","3V3","+3V3_SYS"),("GND","GND","GND"),("BCLK","BCLK","I2S_BCLK"),
        ("LRCL","LRCL","I2S_LRCLK"),("DOUT","DOUT","I2S_DIN"),("SEL","SEL","GND")]),
    dict(ref="U4", value="MAX98357A", fp="Package_DFN_QFN:QFN-16", desc="I2S Class-D amp", pins=[
        ("VIN","VIN","+5V"),("GND","GND","GND"),("BCLK","BCLK","I2S_BCLK"),("LRC","LRC","I2S_LRCLK"),
        ("DIN","DIN","I2S_DOUT"),("GAIN","GAIN","GND"),("SD","SD","+3V3_SYS"),("OUTP","OUT+","SPK_P"),("OUTN","OUT-","SPK_N")]),
    dict(ref="SW1", value="EC11", fp="", desc="Rotary encoder + push", pins=[
        ("A","A","ENC_A"),("B","B","ENC_B"),("C","COM","GND"),("SW","SW","ENC_SW"),("SC","SW_COM","GND")]),
    dict(ref="J1", value="USB-C recept", fp="", desc="Charge in", pins=[
        ("VBUS","VBUS","+VBUS"),("GND","GND","GND"),("CC1","CC1","USB_CC1"),("CC2","CC2","USB_CC2")]),
    dict(ref="J3", value="CSI FFC 15p", fp="", desc="Camera ribbon (CSI-2 bus, not pogo)", pins=[
        ("CSI","CSI_BUS","CSI"),("GND","GND","GND")]),
    dict(ref="CAM1", value="RPi Camera v2", fp="", desc="Fixed camera, looks out optical bore", pins=[
        ("CSI","CSI_BUS","CSI"),("GND","GND","GND")]),
    dict(ref="BT1", value="Li-po 3.7V 1500mAh", fp="", desc="Battery", pins=[("+","+","VBAT"),("-","-","GND")]),
    dict(ref="LS1", value="Speaker 8R 1W", fp="", desc="Speaker", pins=[("+","+","SPK_P"),("-","-","SPK_N")]),
    dict(ref="R1", value="4.7k", fp="Resistor_SMD:R_0402_1005Metric", desc="I2C SDA pull-up", pins=[("1","1","+3V3_SYS"),("2","2","I2C_SDA")]),
    dict(ref="R2", value="4.7k", fp="Resistor_SMD:R_0402_1005Metric", desc="I2C SCL pull-up", pins=[("1","1","+3V3_SYS"),("2","2","I2C_SCL")]),
    dict(ref="R3", value="10k", fp="Resistor_SMD:R_0402_1005Metric", desc="CD# pull-up", pins=[("1","1","+3V3_SYS"),("2","2","CART_CD")]),
    dict(ref="R4", value="10k", fp="Resistor_SMD:R_0402_1005Metric", desc="INT pull-up", pins=[("1","1","+3V3_SYS"),("2","2","CART_INT")]),
    dict(ref="R5", value="100k", fp="Resistor_SMD:R_0402_1005Metric", desc="U5 EN pull-down", pins=[("1","1","CART_VEN"),("2","2","GND")]),
    dict(ref="R7", value="5.1k", fp="Resistor_SMD:R_0402_1005Metric", desc="USB CC1", pins=[("1","1","USB_CC1"),("2","2","GND")]),
    dict(ref="R8", value="5.1k", fp="Resistor_SMD:R_0402_1005Metric", desc="USB CC2", pins=[("1","1","USB_CC2"),("2","2","GND")]),
    dict(ref="J2", value="Pogo 6p (CORE)", fp="", desc="Cartridge interface — connector-spec v0.2", pins=[
        ("1","V+","V+_SW"),("2","GND","GND"),("3","SDA","I2C_SDA"),("4","SCL","I2C_SCL"),("5","CD#","CART_CD"),("6","INT","CART_INT")]),
]

CART = [
    dict(ref="PADS1", value="Pogo pads 6 (CART)", fp="", desc="Mates J2 — connector-spec v0.2", pins=[
        ("1","V+","CV+"),("2","GND","CGND"),("3","SDA","CSDA"),("4","SCL","CSCL"),("5","CD#","CCD"),("6","INT","CINT")]),
    dict(ref="U3", value="24AA02E48 @0x50", fp="Package_TO_SOT_SMD:SOT-23-6", desc="ID EEPROM", pins=[
        ("VCC","VCC","CV+"),("GND","GND","CGND"),("SDA","SDA","CSDA"),("SCL","SCL","CSCL"),
        ("WP","WP","CGND"),("A0","A0","CGND")]),
    dict(ref="LEDR1", value="LED ring 6x + 6x 220R", fp="", desc="Optional ring light (<=150mA budget)", pins=[
        ("A","ANODE","CV+"),("K","CATH","CGND")]),
    dict(ref="SW2", value="Shutter (optional)", fp="", desc="Drives INT low", pins=[("1","1","CINT"),("2","2","CGND")]),
    # CD# hard-tie to GND on the cartridge (presence): a 0R link
    dict(ref="R9", value="0R", fp="Resistor_SMD:R_0402_1005Metric", desc="CD# tie to GND (presence)", pins=[("1","1","CCD"),("2","2","CGND")]),
]


def gen_symbol(c):
    """Rectangular symbol with pins split left/right, on a 2.54 grid."""
    pins = c["pins"]; n = len(pins)
    nl = (n + 1) // 2
    rows = max(nl, n - nl)
    half_h = (rows) * 2.54
    w = 12.7
    ref = c["ref"]
    name = f"VARA:{ref}"          # lib_symbols key (matches instance lib_id)
    sub = ref                       # sub-symbol prefix drops the lib nickname
    s = [f'\t\t(symbol "{name}"',
         '\t\t\t(pin_numbers (hide yes)) (pin_names (offset 1.016))',
         '\t\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)',
         f'\t\t\t(property "Reference" "{c["ref"][0] if c["ref"][0].isalpha() else "U"}" (at 0 {half_h+2.54} 0) (effects (font (size 1.27 1.27))))',
         f'\t\t\t(property "Value" "{c["value"]}" (at 0 {half_h+5.08} 0) (effects (font (size 1.27 1.27))))',
         f'\t\t\t(property "Footprint" "{c["fp"]}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'\t\t\t(property "Description" "{c["desc"]}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'\t\t\t(symbol "{sub}_0_1"',
         f'\t\t\t\t(rectangle (start {-w/2} {half_h}) (end {w/2} {-half_h}) (stroke (width 0.254) (type default)) (fill (type background))))',
         f'\t\t\t(symbol "{sub}_1_1"']
    pin_local = {}
    for i, (num, pname, net) in enumerate(pins):
        if i < nl:                       # left side
            py = half_h - 1.27 - i * 2.54
            px = -w/2 - 5.08; ang = 0
        else:                            # right side
            py = half_h - 1.27 - (i - nl) * 2.54
            px = w/2 + 5.08; ang = 180
        pin_local[num] = (px, py)
        s.append(f'\t\t\t\t(pin passive line (at {px} {py} {ang}) (length 5.08) '
                 f'(name "{pname}" (effects (font (size 1.016 1.016)))) '
                 f'(number "{num}" (effects (font (size 1.016 1.016)))))')
    s.append('\t\t\t))')
    return name, "\n".join(s), pin_local


def gen_sheet(title, comps):
    root = u()
    libdefs, instances, labels = [], [], []
    # grid layout: columns of components
    per_col = 6
    for idx, c in enumerate(comps):
        name, sdef, pin_local = gen_symbol(c)
        libdefs.append(sdef)
        col, row = idx // per_col, idx % per_col
        ox = snap(40 + col * 60); oy = snap(40 + row * 35)
        ref = c["ref"]
        pin_lines = " ".join(f'(pin "{num}" (uuid "{u()}"))' for num, _, _ in c["pins"])
        instances.append(
            f'\t(symbol (lib_id "{name}") (at {ox} {oy} 0) (unit 1)\n'
            f'\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
            f'\t\t(property "Reference" "{ref}" (at {ox-6} {oy-2} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(property "Value" "{c["value"]}" (at {ox-6} {oy+2} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(property "Footprint" "{c["fp"]}" (at {ox} {oy} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'\t\t{pin_lines}\n'
            f'\t\t(instances (project "vara" (path "/{root}" (reference "{ref}") (unit 1)))))')
        for num, pname, net in c["pins"]:
            px, py = pin_local[num]
            # KiCad flips Y when placing a symbol (symbol space +Y up, sheet +Y down):
            wx, wy = snap(ox + px), snap(oy - py)
            shape = "bidirectional"
            ang = 180 if px < 0 else 0
            labels.append(
                f'\t(global_label "{net}" (shape {shape}) (at {wx} {wy} {ang}) '
                f'(effects (font (size 1.016 1.016)) (justify {"right" if px<0 else "left"})) (uuid "{u()}"))')
    libsec = "\n".join(libdefs)
    return (f'(kicad_sch (version 20251024) (generator "vara_gen") (generator_version "10.0")\n'
            f'  (uuid "{root}")\n  (paper "A3")\n'
            f'  (title_block (title "{title}") (date "2026-06-03") (comment 1 "VARA — DESIGN ONLY, not verified"))\n'
            f'  (lib_symbols\n{libsec}\n  )\n'
            + "\n".join(instances) + "\n" + "\n".join(labels) + "\n"
            f'  (sheet_instances (path "/" (page "1")))\n)')


if __name__ == "__main__":
    open("vara_core.kicad_sch", "w").write(gen_sheet("VARA Core", CORE))
    open("vara_cartridge.kicad_sch", "w").write(gen_sheet("VARA Vision Cartridge", CART))
    print("wrote vara_core.kicad_sch + vara_cartridge.kicad_sch")
