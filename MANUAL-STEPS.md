# Manuální kroky pro opravu GPU freeze problémů

## Souhrn problému
NVIDIA GB10 GPU driver (580.95.05) se zasekává, způsobuje soft lockup CPU a zamrznutí systému.

---

## Co bylo automaticky provedeno ✓

1. **GPU Monitoring** - Nastaven cronjob pro logování GPU stavu každých 5 minut
   - Log: `/home/puzik/gpu-monitor.log`

2. **GPU Watchdog skript** - Připraven script pro automatické restartování display manageru při problémech
   - Skript: `/home/puzik/gpu_watchdog.sh`

3. **GRUB konfigurace** - Připraven nový soubor s NVIDIA parametry
   - Nový soubor: `/home/puzik/grub.new`

4. **NVIDIA Bug Report** - Připraven detailní report pro NVIDIA support
   - Report: `/home/puzik/nvidia-bug-report.txt`

---

## Co musíte provést ručně (vyžaduje sudo)

### MOŽNOST 1: Automatická instalace (doporučeno)
```bash
sudo /home/puzik/INSTALL-GPU-FIXES.sh
```

### MOŽNOST 2: Manuální krok za krokem

#### KROK 1: Instalace GPU Watchdog služby
```bash
sudo cp /home/puzik/gpu-watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gpu-watchdog.service
sudo systemctl start gpu-watchdog.service
sudo systemctl status gpu-watchdog.service
```

**Co to dělá:** Watchdog monitoruje NVIDIA chyby v kernel logu. Pokud najde více než 10 chyb, automaticky restartuje `gdm3` (display manager) místo toho, aby systém úplně zamrzl.

---

#### KROK 2: Aktualizace GRUB (kernel parametry)
```bash
# Záloha původního GRUB
sudo cp /etc/default/grub /etc/default/grub.backup

# Instalace nové konfigurace
sudo cp /home/puzik/grub.new /etc/default/grub

# Aktualizace GRUB
sudo update-grub
```

**Přidané parametry:**
- `nvidia-drm.modeset=1` - Zapíná DRM kernel mode setting (stabilnější)
- `nvidia.NVreg_PreserveVideoMemoryAllocations=1` - Zachovává video paměť při suspend/resume

**DŮLEŽITÉ:** Změny se projeví až po restartu systému!

---

#### KROK 3: Downgrade NVIDIA driveru (DOPORUČENO)

**Aktuální:** 580.95.05 (nová verze, obsahuje bugy pro GB10)
**Doporučená:** 550.163.01 (LTS - dlouhodobá podpora, stabilní)

```bash
# Odstranění problematického driveru
sudo apt remove --purge nvidia-driver-580 -y

# Instalace stabilního LTS driveru
sudo apt update
sudo apt install nvidia-driver-550 -y

# Restart systému (NUTNÉ!)
sudo reboot
```

**Alternativně:** Můžete zkusit verze 560 nebo 570, ale 550 LTS je nejstabilnější.

---

#### KROK 4: Sběr logů pro NVIDIA support
```bash
sudo /home/puzik/collect-nvidia-logs.sh
```

**Co se sesbírá:**
- `nvidia-bug-report.log.gz` - Oficiální NVIDIA diagnostický log
- `nvidia-smi-full.txt` - Kompletní GPU informace
- `kernel-nvidia-logs.txt` - Všechny kernel NVIDIA zprávy
- `previous-boot-full.log` - Kompletní log před posledním restartem
- `gpu-pcie-info.txt` - PCIe informace o GPU

---

## Po instalaci

### 1. Restart systému
```bash
sudo reboot
```

### 2. Kontrola po restartu
```bash
# Zkontrolovat GPU watchdog běží
sudo systemctl status gpu-watchdog.service

# Zkontrolovat NVIDIA driver verzi
cat /proc/driver/nvidia/version

# Zkontrolovat GPU funguje
nvidia-smi

# Sledovat watchdog logy
tail -f /var/log/gpu_watchdog.log

# Sledovat GPU monitoring
tail -f /home/puzik/gpu-monitor.log
```

---

## Kontakt NVIDIA Support

### Jak nahlásit problém:

1. **NVIDIA Developer Forums**
   - URL: https://forums.developer.nvidia.com/c/gpu-graphics/linux/148
   - Nové téma: "GB10 GPU freeze on DGX Spark ARM64 - Error 0x0000cb7e"

2. **Co přiložit:**
   - `/home/puzik/nvidia-bug-report.txt` (popis problému)
   - `/home/puzik/nvidia-bug-report.log.gz` (diagnostika)
   - `/home/puzik/previous-boot-full.log` (logy před problémem)

3. **Klíčové informace k uvedení:**
   - Hardware: NVIDIA DGX Spark
   - GPU: GB10 (Device 0x2e12)
   - Platform: ARM64 (aarch64)
   - OS: Ubuntu 24.04.3 LTS
   - Driver: 580.95.05
   - Error code: 0x0000cb7e:6 2:0:4048:4040
   - Issue: Soft lockup, system freeze requiring hard reboot

---

## Dostupné driver verze

```
550.163.01  (LTS - DOPORUČENO)
560.35.05   (Production)
570.195.03  (Production)
575.x       (Server)
580.95.05   (AKTUÁLNÍ - PROBLEMATICKÝ)
```

---

## Monitoring

### Sledování GPU chyb v reálném čase
```bash
journalctl -kf | grep nvidia
```

### Kontrola GPU teploty a využití
```bash
watch -n 1 nvidia-smi
```

### Watchdog logy
```bash
sudo journalctl -u gpu-watchdog.service -f
```

---

## Troubleshooting

### Watchdog služba nejde spustit
```bash
# Zkontrolovat syntax
bash -n /home/puzik/gpu_watchdog.sh

# Zkontrolovat oprávnění
ls -l /home/puzik/gpu_watchdog.sh

# Ručně otestovat
sudo /home/puzik/gpu_watchdog.sh
```

### GRUB se neaktualizoval
```bash
# Zkontrolovat syntax
grep CMDLINE /etc/default/grub

# Znovu aktualizovat
sudo update-grub

# Zkontrolovat výsledný grub.cfg
grep nvidia /boot/grub/grub.cfg
```

### Driver se neinstaloval
```bash
# Zjistit dostupné verze
apt-cache policy nvidia-driver-550

# Zkusit manual instalaci
sudo apt install --reinstall nvidia-driver-550

# Zkontrolovat závislosti
apt-cache depends nvidia-driver-550
```

---

## Reference

- Error code: 0x0000cb7e:6 2:0:4048:4040
- Bug ID: spark-47f9-gb10-freeze-20251126
- Datum prvního výskytu: 2025-11-23
- Frekvence: Několikrát týdně
- Trigger: Pravděpodobně běžné desktop operace (Firefox, Thunderbird)
