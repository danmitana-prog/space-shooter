# space-shooter
2D space shooter hra naprogramovaná v Pythone pomocou Tkinteru a knižnice Pillow.  
Hráč ovláda vesmírnu loď, mieri pomocou myši a strieľa laser, zatiaľ čo uhýba a bojuje proti rôznym typom nepriateľov.

## Features

- Ovládanie lode klávesmi **WASD / šípky**
- Mierenie **crosshairom myši** a streľba s cooldown mechanikou
- Rôzne typy nepriateľov:
  - **Basic** – jednoduchý let smerom dole
  - **Zigzag** – pohyb v sínusovej trajektórii + vlastná farba projektilov
  - **Chaser** – nepriateľ, ktorý priamo naháňa hráča
- Prediktívne strieľanie – nepriatelia sa snažia mieriť tam, kde hráč *bude*
- Animované **projektily (laser)** pomocou GIFu
- **Shield** power-up:
  - Spawnuje sa náhodne na hracej ploche
  - Chráni hráča pred jedným zásahom
  - Aktívny štít je vizuálne zobrazený kruhom okolo lode
- **Hardcore / Classic mód**
  - Classic – viac životov
  - Hardcore – 1 život, žiadny crosshair
- High-score uložené v `scores.json`
- Hlavné menu s:
  - výberom herného módu
  - zobrazením najlepšieho skóre + reset tlačidlom
  - INFO obrazovkou (popis hry zo súboru `info.txt`)

## Controls

- **W / A / S / D alebo šípky** – pohyb lode
- **Myš** – mierenie
- **Ľavé tlačidlo myši** – streľba
- **Space** – pauza / pokračovanie
- **Escape** – vypnutie fullscreen režimu

## Technologies

- Python 3.x
- Tkinter (GUI)
- Pillow (PIL) – práca s obrázkami a animovanými GIFmi
- OOP – triedy `Player`, `Enemy`, `Projectile`, `PlayerBullet`, `Shield`, `Program`
