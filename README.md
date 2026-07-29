# Endstone Scoreboard

Plugin sidebar scoreboard per-player untuk server Endstone (Bedrock).
Author: **Appolo**

## Instalasi

1. Masuk ke folder project ini, lalu build wheel-nya:
   ```
   pip install hatch
   hatch build
   ```
2. Ambil file `.whl` dari folder `dist/`, taruh di folder `plugins/` server Endstone kamu.
3. Jalankan/restart server.

Atau, untuk development, install langsung dari source ke environment Python
yang sama dengan server:
```
pip install -e .
```

## Konfigurasi

Setelah plugin aktif sekali, file `config.toml` akan muncul di
`plugins/endstone_scoreboard/config.toml`. Semua bisa diatur dari situ:

- `enabled` - saklar utama on/off plugin
- `update-interval-ticks` - seberapa sering board di-refresh (20 tick = 1 detik)
- `show-on-join` - apakah board langsung tampil saat player join
- `title` - judul board (support kode warna `&`)
- `lines` - isi baris board, support kode warna `&` dan placeholder:
  `{player}`, `{online}`, `{max}`, `{ping}`, `{level}`, `{tps}`

## Command

- `/sb` - toggle board on/off untuk diri sendiri (default: semua orang bisa)
- `/sbreload` - reload config.toml tanpa restart server (default: op saja)
