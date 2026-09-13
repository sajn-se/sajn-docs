# AI-inställningar för arbetsytan

<!--
slug: settings-ai
audience: Arbetsyteadministratörer
last_verified: 2026-09-13
auto-generated from steps.json — edit the spec, then re-run the runner
-->

AI & Sökning styr hur sajns AI beter sig i en arbetsyta: om den är påslagen, när Bob ska analysera uppladdade PDF:er, om parter får chatta med dokumentet och vilka förslag Bob får lämna. Sidan har tre flikar — AI, Playbook och Sökning & indexering. Guiden visar de två första och ändrar ingenting.

## Innan du börjar

- Du är inloggad och har behörighet att hantera arbetsytans inställningar.
- Sidan går att öppna på alla plan. Bob och AI-textredigering ingår även i Basic; AI-analys av PDF:er, AI-chatt för signerare, förslag och playbook kräver Solo eller högre.
- Inställningarna är arbetsytespecifika — byter du arbetsyta får du en egen uppsättning.

## Steg

### 1. Öppna AI & Sökning i inställningarna

![](../../images/guider/settings-ai/02-oppna.png)

Rutan högst upp sammanfattar datahanteringen: sajn tränar aldrig modeller på ert innehåll, och chattar sparas hos sajn och kan raderas permanent när som helst. Länken Läs mer går till [AI i sajn](/guider/ai), som beskriver exakt vad som skickas och sparas.

Generellt innehåller huvudvalet Aktivera AI-funktioner. Står det Nej stängs allt AI-relaterat av i arbetsytan — chattassistenten, dokumentanalysen och AI-genereringen — och resten av sidan får ingen effekt. Det är rätt ställe att börja om ni av integritets- eller policyskäl inte vill ha AI i en viss arbetsyta.

AI-analys av uppladdade PDF:er bestämmer när Bob ska tolka en uppladdad PDF. Alltid kör analysen direkt och föreslår parter, signeringsinställningar och titel; Manuellt kör ingen analys automatiskt utan låter användaren starta den från dokumentet. PDF:er som kommer in via API:t analyseras aldrig automatiskt — inställningen gäller bara uppladdningar från dashboarden.

AI-chatt för signerare visar en assistent på signeringssidan som svarar på frågor om dokumentet utifrån dokumentet självt. Den kräver att innehållet har indexerats och kan stängas av per dokument.

### 2. Förslag och styrning — vad Bob får föreslå

![](../../images/guider/settings-ai/03-forslag.png)

Varje rad är en typ av förslag Bob får lämna, med sina egna underval. Taggförslag föreslår taggar för färdigsignerade dokument utifrån innehållet, och Endast befintliga taggar begränsar förslagen till arbetsytans befintliga taggar i stället för att hitta på nya. Påminnelseförslag föreslår framåtblickande påminnelser ur färdigsignerade avtal, till exempel inför en prishöjning eller ett uppsägningsfönster. Slår du av ett förslag försvinner även dess underval. Knappen Spara ändringar längst ner tänds först när du ändrat något.

### 3. Fliken Playbook — era riktlinjer för AI:n

![](../../images/guider/settings-ai/06-playbook-flik.png)

Playbooken är det ni alltid kräver, accepterar eller vill få flaggat. Den följs vid granskning och analys av avtal och i chatten med Bob, och ersätter de anpassade instruktioner som tidigare låg på AI-fliken.

Startpaket är färdiga riktlinjer per avtalstyp — sekretessavtal, konsultavtal, leverantörsavtal, anställningsavtal och SaaS-avtal. Välj vilka dokument paketet ska gälla och klicka Lägg till, så kan du ändra det som inte stämmer för er. Under Lägg till riktlinjer skriver du egna, en per rad, eller klistrar in ett helt dokument så delar Bob upp det i riktlinjer som du godkänner innan de sparas. Förslagen under fältet är exempel du kan klicka in direkt.

---

*Senast verifierad: 2026-09-13. Generad av `scripts/guide-runner.ts`.*
