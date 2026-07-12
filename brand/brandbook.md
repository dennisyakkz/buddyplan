# 🎨 Buddyplan Brandbook

Dit handboek bewaakt de visuele identiteit van Buddyplan. De stijl balanceert tussen **technologische betrouwbaarheid (open-source)** en **warme, toegankelijke structuur (zorg/gezin)**.

---

## 1. Kleurenpalet (Color Palette)

Het palet vermijdt harde 'tech-kleuren' (zoals felblauw of neon). In plaats daarvan gebruiken we zachte, organische tinten die rust uitstralen en prettig zijn voor de ogen, wat extra belangrijk is voor de doelgroep.

### Primaire Kleuren (Direct afgestemd op het Master-Logo)
*   **Buddyplan Teal (`#2C6A6B`)**
    *   *Gevoel:* Betrouwbaarheid, rust, zorgzaamheid, stabiliteit.
    *   *Toepassing:* Hoofdkleur, navigatiebalken, primaire actieknoppen, logo-basis (linkerzijde + pijl).
*   **Buddyplan Coral (`#D8745E`)**
    *   *Gevoel:* Warmte, positiviteit, menselijkheid, actie.
    *   *Toepassing:* Accentkleur, secundaire actieknoppen (CTA), highlights, actieve statussen en belangrijke notificaties (rechterzijde + centrale cliënt/kind).

### Elementen van Structuur (De Vierkantjes in het Logo)
De vierkantjes in de figuren staan symbool voor geplande taken en structuur. Ze gebruiken een vaste transparantie-waarde van de hoofdkleuren, wat zorgt voor een rustig van een harmonieus beeld.
*   **Teal Structuur-vierkant:** `#2C6A6B` met **40% opaciteit** (visueel rond `#759B9C` op wit).
*   **Coral Structuur-vierkant:** `#D8745E` met **40% opaciteit** (visueel rond `#ECAAA2` op wit).

### Secundaire & Neutrale Kleuren (Basis UI)
*   **Soft Off-White (`#F7FAFC`)**
    *   *Toepassing:* Standaard achtergrond van de website en applicaties in lichte modus. Voorkomt het kille gevoel van puur wit.
*   **Slate Dark (`#2D3748`)**
    *   *Toepassing:* Hoofdtekst, algemene titels en de merknaam in lichte modus. Biedt een hoog contrast maar is zachter dan puur zwart.
*   **Muted Gray (`#E2E8F0`)**
    *   *Toepassing:* Randen (borders), scheidingslijnen en achtergrond voor inactieve elementen of placeholders.

---

## 2. 🌓 Light & Dark Mode System

Om visuele rust te garanderen en vermoeidheid van de ogen te voorkomen (cruciaal bij always-on wanddisplays en mobiel gebruik onderweg), ondersteunt Buddyplan een volwaardige lichte en donkere modus.

| UI Element | Lichte Modus (Light Mode) | Donkere Modus (Dark Mode) |
| :--- | :--- | :--- |
| **App Achtergrond** | Soft Off-White (`#F7FAFC`) | Deep Charcoal (`#1A202C`) |
| **Card / Container BG** | Pure White (`#FFFFFF`) | Slate Gray (`#2D3748`) |
| **Hoofdtekst / Titels** | Slate Dark (`#2D3748`) | Pale Gray (`#EDF2F7`) |
| **Subtekst / Labels** | Muted Slate (`#718096`) | Light Muted Gray (`#A0AEC0`) |
| **Borders / Scheidslijnen**| Muted Gray (`#E2E8F0`) | Dark Border Gray (`#4A5568`) |
| **Navigatiebalk (Header)** | Buddyplan Teal (`#2C6A6B`) | Dark Teal (`#1F4A4B`) |

---

## 3. 📅 Agenda & Taken Flexibel Kleurenpalet

Op het dashboard krijgen taken een persoonsgebonden achtergrondkleur. In de agenda kan de gebruiker zelf een kleur uit het palet kiezen om verschillende soorten evenementen (zoals werk, school of persoonlijke afspraken) te onderscheiden. 

Om in beide modi aan de WCAG-toegankelijkheidsnormen te voldoen, is elk palet-item opgebouwd uit een specifieke combinatie van achtergrond (BG) en tekstkleur.

### Lichte Modus (Donkere tekst op lichte pastel-achtergrond)
*   🔴 **Koraal / Rood:** BG `#FED7D7` \| Tekst `#9B2C2C`
*   🟠 **Oranje:** BG `#FEEBC8` \| Tekst `#9C4221`
*   🟡 **Geel:** BG `#FEFCBF` \| Tekst `#744210`
*   🟢 **Groen:** BG `#C6F6D5` \| Tekst `#22543D`
*   🔵 **Blauw:** BG `#EBF8FF` \| Tekst `#2B6CB0`
*   🟢 **Teal (Standaard):** BG `#E6FFFA` \| Tekst `#234E52`
*   🟣 **Paars:** BG `#EBF4FF` \| Tekst `#4C51BF`
*   🟤 **Bruin:** BG `#EDF2F7` \| Tekst `#4A5568`

### Donkere Modus (Lichte tekst op diepe achtergrond)
*   🔴 **Koraal / Rood:** BG `#9B2C2C` \| Tekst `#FFF5F5`
*   🟠 **Oranje:** BG `#9C4221` \| Tekst `#FFFAF0`
*   🟡 **Geel:** BG `#744210` \| Tekst `#FFFFF0`
*   🟢 **Groen:** BG `#22543D` \| Tekst `#F0FFF4`
*   🔵 **Blauw:** BG `#2B6CB0` \| Tekst `#EBF8FF`
*   🟢 **Teal (Standaard):** BG `#234E52` \| Tekst `#E6FFFA`
*   🟣 **Paars:** BG `#4C51BF` \| Tekst `#EBF4FF`
*   🟤 **Bruin:** BG `#4A5568` \| Tekst `#F7FAFC`

---

## 4. Typografie (Typography)

Voor een applicatie die draait om planning en structuur is leesbaarheid essentieel. We kiezen voor moderne, schreefloze (sans-serif) lettertypes die gratis beschikbaar zijn via Google Fonts.

### Kopteksten (Headings) & Logo-tekst
*   **Lettertype:** **Plus Jakarta Sans** (of als fallback **Inter**)
*   **Dikte (Weight):** Bold (`700`) of Semi-Bold (`600`)
*   **Kenmerken:** Modern, geometrisch maar met vriendelijke, open rondingen.
*   **Toepassing:** H1 t/m H4 titels op de website, in de documentatie en in de apps. Paginatitels worden *nooit* in paars of blauw weergegeven, maar volgen de text-tokens uit het Light/Dark-systeem.

### Broodtekst (Body text) & UI
*   **Lettertype:** **Inter** (Regular `400` / Medium `500`)
*   **Kenmerken:** Extreem hoge leesbaarheid, ook op kleinere schermen zoals telefoons en wandtablets. Perfect voor lijsten en agenda-items.
*   **Toepassing:** Paragrafen, taakbeschrijvingen, menu's, formuliervelden en labels.

---

## 5. UI/UX Stijlelementen (Design Tokens)

Om de visuele warmte uit het logo door te trekken in de software, hanteren we de volgende design-richtlijnen:

*   **Afgeronde Hoeken (Border Radius):**
    *   Gebruik royale afronding voor een vriendelijke, benaderbare uitstraling.
    *   *Knoppen, Inputs en Cards:* `border-radius: 12px;` (Tailwind: `rounded-xl`)
    *   *Modals en Wanddisplays:* `border-radius: 16px;` (Tailwind: `rounded-2xl`)
*   **Schaduwen (Shadows):**
    *   Subtiel en zacht, geen harde zwarte lijnen of diepe schaduwen.
    *   *Tailwind CSS:* `shadow-sm` of `shadow-md` met een zeer lage opaciteit (bijv. `rgba(0, 0, 0, 0.04)`).
*   **Visuals & Iconen:**
    *   Gebruik altijd gevulde of dikke, afgeronde iconen (bijv. *Lucide Icons* of *Heroicons* met afgeronde hoeken). Dit helpt kinderen en cliënten met een verstandelijke beperking bij de snelle visuele herkenning.

---

## 6. Toepassing per Component & Interactie

### Invoervelden (Inputs & Dropdowns)
*   **Achtergrond:** Wit (`#FFFFFF`) in Light Mode, Slate Gray (`#2D3748`) in Dark Mode. Randen gebruiken het bijbehorende border-token.
*   **Focus State:** Wanneer een veld actief is, wordt de rand **Buddyplan Teal (`#2C6A6B`)** met een subtiele, zachte glow (`box-shadow`).
*   **Hoeken:** Conform de richtlijn `rounded-xl` (12px).

### Switches & Toggles (Formulier opties)
*   **Inactief (Uit):** Achtergrond Muted Gray (`#E2E8F0` / `#4A5568`) met een witte schuifknop.
*   **Actief (Aan):** Achtergrond activeert in **Buddyplan Teal (`#2C6A6B`)** of **Buddyplan Coral (`#D8745E`)**.

### Knoppen (Buttons)
*   **Primaire Acties (Opslaan, + Nieuwe taak):** Vaste achtergrond van `#2C6A6B` met witte tekst.
*   **Gevaar Acties (Verwijderen):** Achtergrond `#E53E3E` met witte tekst.
*   **Navigatie Knoppen / Tabs:** Actieve statussen in de header krijgen een subtiele transparante witte achtergrond (`rgba(255, 255, 255, 0.15)`).

### Buddyplan Display (Wandtablet)
*   De 'cards' voor de gezinsleden of taken gebruiken de 40% opaciteit-varianten (of de lichte/donkere combinaties uit het flexibele palet) als achtergrond, omringd door voldoende witruimte (*padding*) om overprikkeling tegen te gaan.

---

## 7. 🏷️ Instructies voor het Renderen van de Merknaam (Tekst + Logo)

Om maximale flexibiliteit, scherpte en perfecte Dark Mode-ondersteuning te garanderen, wordt de merknaam "Buddyplan" **nooit** als afbeelding gerenderd. Het master-logo (SVG) bevat uitsluitend het grafische symbool (het huis met de poppetjes). De tekst wordt hier in de code live als CSS/HTML-element tegenaan gezet.

### Typografische Regels voor "Buddyplan"
*   **Lettertype:** `Plus Jakarta Sans`
*   **Dikte:** Bold (`font-weight: 700`)
*   **Spatiëring:** `letter-spacing: -0.02em` (subtiele tight tracking voor een compact, modern logo-gevoel).
*   **Kast:** Altijd beginnen met een hoofdletter, gevolgd door kleine letters: **Buddyplan** (geen volledige HOOFDLETTERS).

### Kleurtoepassing op basis van Context

1.  **In de App Header (Navigatiebalk):**
    *   *Light & Dark mode:* Omdat de header in beide modi een donkere Teal-achtergrond heeft, wordt de tekst hier altijd in **Pure White (`#FFFFFF`)** gerenderd naast het icoon.
2.  **Op de Login-pagina & Landingssite (Lichte ondergrond):**
    *   De tekst kleurt mee met het standaardsysteem en wordt gerenderd in **Slate Dark (`#2D3748`)**.
3.  **Op de Login-pagina & Landingssite (Donkere ondergrond):**
    *   De tekst kleurt mee met de Dark Mode en switcht naar **Pale Gray (`#EDF2F7`)**.

### Lay-out & Compositie (Tailwind Blueprints)

#### A. Horizontale Compositie (Liggend - Toepassing: Header / Navbalk)
Het icoon staat links, de tekst staat rechts. Op mobiele apparaten verbergt de tekst zich dynamisch (`hidden md:block`) om ruimte te besparen.

```html
<div class="flex items-center gap-3">
  <!-- Master Logo Symbool (Alleen SVG) -->
  <img src="/branding/buddyplan-icon.svg" class="h-8 w-8" alt="Buddyplan Logo" />
  
  <!-- Merknaam als pure HTML-tekst -->
  <span class="hidden md:block font-['Plus_Jakarta_Sans'] font-bold text-xl tracking-tight text-white">
    Buddyplan
  </span>
</div>
```

### 7.1 Logo-variaties op Gekleurde Achtergronden (Inverse Logo)

Wanneer het logo geplaatst wordt op een donkere of gekleurde achtergrond die (deels) overeenkomt met de primaire merkkleuren — zoals de **Buddyplan Teal (`#2C6A6B`)** headerbalk — mag het originele gekleurde logo **niet** worden gebruikt wegens het wegvallen van het contrast.

#### De Oplossing: Buddyplan Logo Inverse (Wit)
In deze specifieke situaties gebruikt de applicatie een volledig monochrome, witte variant van het transparante SVG-icoon.

*   **Lijnen en Vlakken:** Alle gekleurde elementen (zowel het Teal- als het Coral-gedeelte van het huis en de gezinsleden) worden omgezet naar **Pure White (`#FFFFFF`)**.
*   **De Vierkantjes (Placeholders):** Om de symboliek en diepte te behouden, krijgen de vierkantjes in deze witte variant een opaciteit van **30% wit** (`rgba(255, 255, 255, 0.3)`).

#### Technische Implementatie voor de Developer
Als de developer een schone, inline SVG gebruikt, hoeft er geen apart afbeeldingsbestand te worden ingeladen. De developer kan via CSS/Tailwind de `fill`-eigenschappen van de SVG-paden binnen de header direct overschrijven:

```css
/* Zorg dat de hoofdlijnen van de SVG in de header wit kleuren */
.header-logo svg path.logo-body {
    fill: #ffffff;
}

/* Zorg dat de elementen die transparant horen te zijn 30% wit worden */
.header-logo svg path.logo-square {
    fill: rgba(255, 255, 255, 0.3);
}
```# 🎨 Buddyplan Brandbook

Dit handboek bewaakt de visuele identiteit van Buddyplan. De stijl balanceert tussen **technologische betrouwbaarheid (open-source)** en **warme, toegankelijke structuur (zorg/gezin)**.

---

## 1. Kleurenpalet (Color Palette)

Het palet vermijdt harde 'tech-kleuren' (zoals felblauw of neon). In plaats daarvan gebruiken we zachte, organische tinten die rust uitstralen en prettig zijn voor de ogen, wat extra belangrijk is voor de doelgroep.

### Primaire Kleuren (Direct afgestemd op het Master-Logo)
*   **Buddyplan Teal (`#2C6A6B`)**
    *   *Gevoel:* Betrouwbaarheid, rust, zorgzaamheid, stabiliteit.
    *   *Toepassing:* Hoofdkleur, navigatiebalken, primaire actieknoppen, logo-basis (linkerzijde + pijl).
*   **Buddyplan Coral (`#D8745E`)**
    *   *Gevoel:* Warmte, positiviteit, menselijkheid, actie.
    *   *Toepassing:* Accentkleur, secundaire actieknoppen (CTA), highlights, actieve statussen en belangrijke notificaties (rechterzijde + centrale cliënt/kind).

### Elementen van Structuur (De Vierkantjes in het Logo)
De vierkantjes in de figuren staan symbool voor geplande taken en structuur. Ze gebruiken een vaste transparantie-waarde van de hoofdkleuren, wat zorgt voor een rustig van een harmonieus beeld.
*   **Teal Structuur-vierkant:** `#2C6A6B` met **40% opaciteit** (visueel rond `#759B9C` op wit).
*   **Coral Structuur-vierkant:** `#D8745E` met **40% opaciteit** (visueel rond `#ECAAA2` op wit).

### Secundaire & Neutrale Kleuren (Basis UI)
*   **Soft Off-White (`#F7FAFC`)**
    *   *Toepassing:* Standaard achtergrond van de website en applicaties in lichte modus. Voorkomt het kille gevoel van puur wit.
*   **Slate Dark (`#2D3748`)**
    *   *Toepassing:* Hoofdtekst, algemene titels en de merknaam in lichte modus. Biedt een hoog contrast maar is zachter dan puur zwart.
*   **Muted Gray (`#E2E8F0`)**
    *   *Toepassing:* Randen (borders), scheidingslijnen en achtergrond voor inactieve elementen of placeholders.

---

## 2. 🌓 Light & Dark Mode System

Om visuele rust te garanderen en vermoeidheid van de ogen te voorkomen (cruciaal bij always-on wanddisplays en mobiel gebruik onderweg), ondersteunt Buddyplan een volwaardige lichte en donkere modus.

| UI Element | Lichte Modus (Light Mode) | Donkere Modus (Dark Mode) |
| :--- | :--- | :--- |
| **App Achtergrond** | Soft Off-White (`#F7FAFC`) | Deep Charcoal (`#1A202C`) |
| **Card / Container BG** | Pure White (`#FFFFFF`) | Slate Gray (`#2D3748`) |
| **Hoofdtekst / Titels** | Slate Dark (`#2D3748`) | Pale Gray (`#EDF2F7`) |
| **Subtekst / Labels** | Muted Slate (`#718096`) | Light Muted Gray (`#A0AEC0`) |
| **Borders / Scheidslijnen**| Muted Gray (`#E2E8F0`) | Dark Border Gray (`#4A5568`) |
| **Navigatiebalk (Header)** | Buddyplan Teal (`#2C6A6B`) | Dark Teal (`#1F4A4B`) |

---

## 3. 📅 Agenda & Taken Flexibel Kleurenpalet

Op het dashboard krijgen taken een persoonsgebonden achtergrondkleur. In de agenda kan de gebruiker zelf een kleur uit het palet kiezen om verschillende soorten evenementen (zoals werk, school of persoonlijke afspraken) te onderscheiden. 

Om in beide modi aan de WCAG-toegankelijkheidsnormen te voldoen, is elk palet-item opgebouwd uit een specifieke combinatie van achtergrond (BG) en tekstkleur.

### Lichte Modus (Donkere tekst op lichte pastel-achtergrond)
*   🔴 **Koraal / Rood:** BG `#FED7D7` \| Tekst `#9B2C2C`
*   🟠 **Oranje:** BG `#FEEBC8` \| Tekst `#9C4221`
*   🟡 **Geel:** BG `#FEFCBF` \| Tekst `#744210`
*   🟢 **Groen:** BG `#C6F6D5` \| Tekst `#22543D`
*   🔵 **Blauw:** BG `#EBF8FF` \| Tekst `#2B6CB0`
*   🟢 **Teal (Standaard):** BG `#E6FFFA` \| Tekst `#234E52`
*   🟣 **Paars:** BG `#EBF4FF` \| Tekst `#4C51BF`
*   🟤 **Bruin:** BG `#EDF2F7` \| Tekst `#4A5568`

### Donkere Modus (Lichte tekst op diepe achtergrond)
*   🔴 **Koraal / Rood:** BG `#9B2C2C` \| Tekst `#FFF5F5`
*   🟠 **Oranje:** BG `#9C4221` \| Tekst `#FFFAF0`
*   🟡 **Geel:** BG `#744210` \| Tekst `#FFFFF0`
*   🟢 **Groen:** BG `#22543D` \| Tekst `#F0FFF4`
*   🔵 **Blauw:** BG `#2B6CB0` \| Tekst `#EBF8FF`
*   🟢 **Teal (Standaard):** BG `#234E52` \| Tekst `#E6FFFA`
*   🟣 **Paars:** BG `#4C51BF` \| Tekst `#EBF4FF`
*   🟤 **Bruin:** BG `#4A5568` \| Tekst `#F7FAFC`

---

## 4. Typografie (Typography)

Voor een applicatie die draait om planning en structuur is leesbaarheid essentieel. We kiezen voor moderne, schreefloze (sans-serif) lettertypes die gratis beschikbaar zijn via Google Fonts.

### Kopteksten (Headings) & Logo-tekst
*   **Lettertype:** **Plus Jakarta Sans** (of als fallback **Inter**)
*   **Dikte (Weight):** Bold (`700`) of Semi-Bold (`600`)
*   **Kenmerken:** Modern, geometrisch maar met vriendelijke, open rondingen.
*   **Toepassing:** H1 t/m H4 titels op de website, in de documentatie en in de apps. Paginatitels worden *nooit* in paars of blauw weergegeven, maar volgen de text-tokens uit het Light/Dark-systeem.

### Broodtekst (Body text) & UI
*   **Lettertype:** **Inter** (Regular `400` / Medium `500`)
*   **Kenmerken:** Extreem hoge leesbaarheid, ook op kleinere schermen zoals telefoons en wandtablets. Perfect voor lijsten en agenda-items.
*   **Toepassing:** Paragrafen, taakbeschrijvingen, menu's, formuliervelden en labels.

---

## 5. UI/UX Stijlelementen (Design Tokens)

Om de visuele warmte uit het logo door te trekken in de software, hanteren we de volgende design-richtlijnen:

*   **Afgeronde Hoeken (Border Radius):**
    *   Gebruik royale afronding voor een vriendelijke, benaderbare uitstraling.
    *   *Knoppen, Inputs en Cards:* `border-radius: 12px;` (Tailwind: `rounded-xl`)
    *   *Modals en Wanddisplays:* `border-radius: 16px;` (Tailwind: `rounded-2xl`)
*   **Schaduwen (Shadows):**
    *   Subtiel en zacht, geen harde zwarte lijnen of diepe schaduwen.
    *   *Tailwind CSS:* `shadow-sm` of `shadow-md` met een zeer lage opaciteit (bijv. `rgba(0, 0, 0, 0.04)`).
*   **Visuals & Iconen:**
    *   Gebruik altijd gevulde of dikke, afgeronde iconen (bijv. *Lucide Icons* of *Heroicons* met afgeronde hoeken). Dit helpt kinderen en cliënten met een verstandelijke beperking bij de snelle visuele herkenning.

---

## 6. Toepassing per Component & Interactie

### Invoervelden (Inputs & Dropdowns)
*   **Achtergrond:** Wit (`#FFFFFF`) in Light Mode, Slate Gray (`#2D3748`) in Dark Mode. Randen gebruiken het bijbehorende border-token.
*   **Focus State:** Wanneer een veld actief is, wordt de rand **Buddyplan Teal (`#2C6A6B`)** met een subtiele, zachte glow (`box-shadow`).
*   **Hoeken:** Conform de richtlijn `rounded-xl` (12px).

### Switches & Toggles (Formulier opties)
*   **Inactief (Uit):** Achtergrond Muted Gray (`#E2E8F0` / `#4A5568`) met een witte schuifknop.
*   **Actief (Aan):** Achtergrond activeert in **Buddyplan Teal (`#2C6A6B`)** of **Buddyplan Coral (`#D8745E`)**.

### Knoppen (Buttons)
*   **Primaire Acties (Opslaan, + Nieuwe taak):** Vaste achtergrond van `#2C6A6B` met witte tekst.
*   **Gevaar Acties (Verwijderen):** Achtergrond `#E53E3E` met witte tekst.
*   **Navigatie Knoppen / Tabs:** Actieve statussen in de header krijgen een subtiele transparante witte achtergrond (`rgba(255, 255, 255, 0.15)`).

### Buddyplan Display (Wandtablet)
*   De 'cards' voor de gezinsleden of taken gebruiken de 40% opaciteit-varianten (of de lichte/donkere combinaties uit het flexibele palet) als achtergrond, omringd door voldoende witruimte (*padding*) om overprikkeling tegen te gaan.

---

## 7. 🏷️ Instructies voor het Renderen van de Merknaam (Tekst + Logo)

Om maximale flexibiliteit, scherpte en perfecte Dark Mode-ondersteuning te garanderen, wordt de merknaam "Buddyplan" **nooit** als afbeelding gerenderd. Het master-logo (SVG) bevat uitsluitend het grafische symbool (het huis met de poppetjes). De tekst wordt hier in de code live als CSS/HTML-element tegenaan gezet.

### Typografische Regels voor "Buddyplan"
*   **Lettertype:** `Plus Jakarta Sans`
*   **Dikte:** Bold (`font-weight: 700`)
*   **Spatiëring:** `letter-spacing: -0.02em` (subtiele tight tracking voor een compact, modern logo-gevoel).
*   **Kast:** Altijd beginnen met een hoofdletter, gevolgd door kleine letters: **Buddyplan** (geen volledige HOOFDLETTERS).

### Kleurtoepassing op basis van Context

1.  **In de App Header (Navigatiebalk):**
    *   *Light & Dark mode:* Omdat de header in beide modi een donkere Teal-achtergrond heeft, wordt de tekst hier altijd in **Pure White (`#FFFFFF`)** gerenderd naast het icoon.
2.  **Op de Login-pagina & Landingssite (Lichte ondergrond):**
    *   De tekst kleurt mee met het standaardsysteem en wordt gerenderd in **Slate Dark (`#2D3748`)**.
3.  **Op de Login-pagina & Landingssite (Donkere ondergrond):**
    *   De tekst kleurt mee met de Dark Mode en switcht naar **Pale Gray (`#EDF2F7`)**.

### Lay-out & Compositie (Tailwind Blueprints)

#### A. Horizontale Compositie (Liggend - Toepassing: Header / Navbalk)
Het icoon staat links, de tekst staat rechts. Op mobiele apparaten verbergt de tekst zich dynamisch (`hidden md:block`) om ruimte te besparen.

```html
<div class="flex items-center gap-3">
  <!-- Master Logo Symbool (Alleen SVG) -->
  <img src="/branding/buddyplan-icon.svg" class="h-8 w-8" alt="Buddyplan Logo" />
  
  <!-- Merknaam als pure HTML-tekst -->
  <span class="hidden md:block font-['Plus_Jakarta_Sans'] font-bold text-xl tracking-tight text-white">
    Buddyplan
  </span>
</div>
```

### 7.1 Logo-variaties op Gekleurde Achtergronden (Inverse Logo)

Wanneer het logo geplaatst wordt op een donkere of gekleurde achtergrond die (deels) overeenkomt met de primaire merkkleuren — zoals de **Buddyplan Teal (`#2C6A6B`)** headerbalk — mag het originele gekleurde logo **niet** worden gebruikt wegens het wegvallen van het contrast.

#### De Oplossing: Buddyplan Logo Inverse (Wit)
In deze specifieke situaties gebruikt de applicatie een volledig monochrome, witte variant van het transparante SVG-icoon.

*   **Lijnen en Vlakken:** Alle gekleurde elementen (zowel het Teal- als het Coral-gedeelte van het huis en de gezinsleden) worden omgezet naar **Pure White (`#FFFFFF`)**.
*   **De Vierkantjes (Placeholders):** Om de symboliek en diepte te behouden, krijgen de vierkantjes in deze witte variant een opaciteit van **30% wit** (`rgba(255, 255, 255, 0.3)`).

#### Technische Implementatie voor de Developer
Als de developer een schone, inline SVG gebruikt, hoeft er geen apart afbeeldingsbestand te worden ingeladen. De developer kan via CSS/Tailwind de `fill`-eigenschappen van de SVG-paden binnen de header direct overschrijven:

```css
/* Zorg dat de hoofdlijnen van de SVG in de header wit kleuren */
.header-logo svg path.logo-body {
    fill: #ffffff;
}

/* Zorg dat de elementen die transparant horen te zijn 30% wit worden */
.header-logo svg path.logo-square {
    fill: rgba(255, 255, 255, 0.3);
}
```
