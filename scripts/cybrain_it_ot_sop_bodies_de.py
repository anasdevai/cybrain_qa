# Volltexte (Deutsch) für SOP-IT-001 .. 005 – Quelle: Cybrain IT/OT Hyaluron-Referenz
# Dient content_json (TipTap) und semantischer BGE-Indexierung.

SOP_S001 = r"""SOP-IT-001: Zugriffsmanagement auf Produktionsnetzwerk (OT). Version 3.1, Status: wirksam, Fachbereich: IT/Produktion/QA, GMP-Kritikalität: hoch.
1. Zweck: Sicherstellung, dass nur autorisierte Personen auf das Produktionsnetzwerk (OT) zugreifen können. Trennung von IT- (Büro) und OT-Netzwerk (Produktion) nach IEC 62443.
2. Geltungsbereich: eigene IT-Mitarbeiter; externe IT-Dienstleister (Netzwerkwartung, Maschinenhersteller); Produktionsmitarbeiter mit SPS/SCADA-Zugang; Wartungspersonal (Siemens, Rockwell, B. Braun, Sartorius); KI-Systeme mit Zugriff auf Produktionsdaten.
3. Verantwortlichkeiten: IT-Sicherheitsbeauftragter – Vergabe/Entzug, Log-Monitoring, wöchentliche Reviews. Produktionsleitung – Freigaben für eigene Mitarbeiter, monatliche Bestätigung. QA – Prüfung der Zugriffslogs bei Audits, vierteljährliche Stichproben. Externer Dienstleister – Einhaltung, Dokumentation, jährliche Unterweisung. KI-Administrator – IAM für KI-Zugriffe, separate Logführung.
4. Verfahren: 4.1 Zugriffsarten OT: Read-only (Sicht Prozessdaten, IT, automatisches Log); Operator (Start/Stopp, Abruf, Produktion, manuelles+automatisches Log); Service (Wartung, Kalibrierung, IT+QA, doppeltes Log); Admin (Firmware, IT-Sicherheit+QP, Vier-Augen); KI-Read (Echtzeitdaten PM, KI-Admin+IT, API-Log); KI-Write (Parameter-Rückschreiben, QA+Produktion, Freigabepflicht). 4.2 Externe: Anmeldung 24h vorher beim IT-Sicherheitsbeauftragten; Vertraulichkeitsvereinbarung inkl. GMP; Session max. 8h, Verlängerung mit QA; Remote nur VPN mit 2FA (Hardware/Biometrie); Nach Sitzung Löschung/Protokoll 1h; externe Zugänge jährlich QA-Review. 4.3 Passwort OT: min. 12 Zeichen, mind. 3/4 Kategorien, 90 Tage, 10 Altpasswörter, keine Standard-Defaults, 3 Fehlversuche/15 min Sperre, Service-Accounts bevorzugt Zertifikat. 4.4 Audit Trail: Einträge inkl. Benutzer, UTC-Zeit, IP, Geräte-ID, Grund, Dauer, Genehmiger (bei Schreibzugriff), Aufbewahrung 6 Jahre. 4.5 Break-Glass: kritischer Störfall, Token im Tresor (Produktionsleiter+QA), Nachdokumentation 24h, sonst Management-Meldung.
5. Regulatorische Anbindung: Verknüpfung SOP-IT-002, SOP-IT-003, SOP-IT-004, SOP-IT-005, SOP-QA-002 (Abweichung).
Referenz-Abweichungssätze: Unbefugter Zugriff, fehlendes 2FA, lückenhafte Logs, übermäßige Rechte, fehlende Vertraulichkeitsdokumentation, Nachweis SOP-IT-001.
"""

SOP_S002 = r"""SOP-IT-002: Netzwerksicherheit & Firewall (OT/IT-Trennung). Version 2.2, Fachbereich: IT/OT, Status: wirksam.
1. Zweck: Schutz des Produktionsnetzwerks vor unbefugten Zugriffen aus dem Büro (IT) und dem Internet.
2. Geltungsbereich: IT–OT-Firewall; interne OT-Segmente (Fermentation, Aufreinigung, Abfüllung, Labor); Dienstleister-Remote; Produktions-WLAN mit getrennter, verschlüsselter SSID.
3. Rollen: Netzwerkadmin (Konfiguration, Monitoring, wöchentliche Regel-Reviews); IT-Sicherheit (Penetrationstest halbjährlich); QA (Freigabe von Firewall-Änderungen, Nachweis).
4. Regeln: IT→OT nur 443/HTTPS für definiertes Read-only-Monitoring, 22/SSH nur abgesichert für Wartung; kein Internet→OT; VPN→OT nur 443/22 mit Freigabe. OT-intern: Fermentation, Aufreinigung, Abfüllung, Labor klar getrennt; bekannte Dienstleisterpfad über VPN, kein ad-hoc-TeamViewer. Monitoring: zentrales SIEM, Alarme bei Massen-Connection aus Internet, Zugriff 20:00–06:00, unbekannten Endgeräten, Reaktion 30 min bei Kritik.
5. Kritische Abweichung: bewusstes Umgehen der Trennung (Direktkabel IT–OT) führt sofortiger Stilllegung/Isolation bis QA-Freigabe. Referenz: Segmentierung, Alarmierung, Wlan-Härtung, unbekannte IP im OT, permissive Regeln.
"""

SOP_S003 = r"""SOP-IT-003: Notfallzugriff (Break-Glass) auf OT-Systeme. Version 1.4, Fachbereich: IT/QA/Produktion, Status: wirksam.
1. Zweck: kontrollierter, dokumentierter Zugriff bei längerem Produktionsstillstand oder Ausfall regulärer Authentifizierung, wenn kein standard IT-Admin erreichbar ist.
2. Geltungsbereich: Stillstand länger 30 min; zentraler Authentisierungsausfall; vollständige Nichtverfügbarkeit regulärer Prozesse. Kein Ersatz für Routine-Administration.
3. Abläufe: Notfall-Token (YubiKey) in getrennt versiegelten Umschlägen, Tresorzugriff ausschließlich Produktionsleitung und QA, Zwei-Personen-Logik, Aktivierung gemeinsam am Terminal, maximale Sitzung 2 Stunden, nachgelagert QMS-Eintrag, Bestellung neuer Token, Eskalation bei Lücken.
4. Schulung: halbjährliche Übung für definierte Rollen; Sichtkontrolle der Umschläge; Sperre bei offenen Verstößen.
5. Fachkontext: SOP-IT-001/002 (Nachträgliche IAM-/Netz-Abgleiche). Typische Befundrichtungen: fehlende Nachdokumentation, beschädigter Umschlag, Trennungsprinzip in Zweifel gezogen, fehlendes Token-Recycling, veraltete Umschlag-Nummerierung, brüchige Video- oder Zutrittsprotokolle, Termin-Compliance Schulungsmatrix.
"""

SOP_S004 = r"""SOP-IT-004: KI-Systeme in der Produktion (Predictive Maintenance, Prozesssteuerung). Version 1.0, Status: in Freigabe (Entwurf), Fachbereich: IT, Data Science, QA.
1. Zweck: einheitliche GMP- und Sicherheitskriterien für KI, die Fertigungs- und Umfelddaten lesen, Empfehlungen geben oder eingrenzte Sollwertkorrekturen fahren, speziell Hyloronsäure-Profile (Rührverhalten, pH, Viskosität) und Linien-Assets (Abfüllung, Chromatographie).
2. Geltung: KI-Read, KI-Recommend, KI-Automate mit Grenzkurven, alle vor Produktionseinsatz validieren; Logging der Modell-IDs, Trainings-Snapshot, Signatur, Rollback, Override-Pfad.
3. Zuständigkeiten: Data Science (Entwicklung, Validationspaket); KI-Admin (Infrastruktur, IAM, sichere Pipelines); QA/Pharma (Risikobewertung, SLOs, Freigabepunkte); Produktionsleitung (Echtzeit-Override, Eskalation).
4. Fachliche Schranken: Temperatur ±2 °C, pH ±0,2, Rührung ±10 %, sonst harter Stopp und Alarm. Kein Einsatz nicht final freigegebener Modelle; vollständiges API-Logging, adversarielle Stichproben, Rückfallebene in manuelle SOP-Steuerung, Charge-Freigabe abhängig von QA-Bewertung, Behördenpfade bei kritischer Abweichung. Referenzen: SOP-IT-001, SOP-IT-005, Abweichungs- und Rückruf-Playbooks.
"""

SOP_S005 = r"""SOP-IT-005: Patch-Management für OT und eingebettete Fertigungs-IT. Version 2.0, Fachbereich: IT/OT, Status: wirksam.
1. Zweck: zeitgerechtes Schließen sicherheitskritischer Lücken auf SCADA, SPS, HMI, vernetzten Zellen-Switches und KI-Servern, ohne laufende Chargen zu gefährden.
2. Geltung: vollumfänglich inkl. S7-/ControlLogix-Steuerungen, HMI, Fortinet, Cisco, KI-Runtime (Ubuntu), WinCC, Patch-Journal, Rollback, Change Advisory Board mit QA.
3. SLAs: CVE ≥9 / RCE: 48 h; 7.0–8.9: 7 Tage; 4.0–6.9: 30 Tage; niedriger: 90 Tage, sofern keine laufende Charge-Abhängigkeit. Kein Patch während laufender Charge außer Ausnahmeverfahren, dann QA-Freigabe, dokumentierter Downtime-Plan, Backup, Funktionstest.
4. Prozess: Scanner, Impact-Rating mit Produktion, 24 h Test auf Parity-Stack, Freigabe, Sonntag 02:00–06:00 Rollout, Verifikation, Rollback. Ausnahmejournal im QMS. Referenzen: SIEM, Asset-Inventar, SOP-IT-002, Verknüpfte Abweichungen: überschrittene 48h-Frist, ungetesteter Patch, Rollback-Defizit, beendete Lizenzen, Kommunikationslücken vor Charge-Stillstand, Backup ausstehend, Patch während laufendem Batch ohne Genehmigung.
5. Wirtschaft: Budget für Testlandschaft und Snapshot-Systeme, Kopplung an SOP-IT-004, wenn KI-Laufzeit gepatcht werden muss.
"""
