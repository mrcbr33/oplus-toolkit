"""
i18n.py - Internationalization strings for OPlus Toolkit (EN/IT).
"""

from __future__ import annotations


I18N: dict[str, dict[str, str]] = {
    "en": {
        # App
        "app_title": "OPlus Toolkit",
        "app_subtitle": "Debloater for ColorOS, OxygenOS and Realme UI",

        # Sidebar
        "nav_dashboard": "Dashboard",
        "nav_debloater": "Debloater",
        "nav_packages": "All Packages",
        "nav_backups": "Backups",
        "nav_settings": "Settings",

        # Status
        "status_ready": "Ready.",
        "status_scanning": "Scanning device...",
        "status_no_device": "No device connected.",
        "status_adb_missing": "ADB not found in PATH.",
        "status_connected": "Connected to {model}",
        "status_backup_saved": "Backup saved: {name}",
        "status_processing": "Processing {i}/{n}...",
        "status_error": "Error: {msg}",
        "status_adb_restarted": "ADB server restarted.",
        "status_loaded_packages": "Loaded {n} packages.",

        # Dashboard
        "dash_title": "Device Dashboard",
        "dash_refresh": "Refresh device info",
        "dash_restart_adb": "Restart ADB server",
        "dash_no_device": "No device connected.\nConnect a device via USB and enable USB debugging.",
        "dash_adb_missing": "ADB not installed.",

        # Debloater
        "deb_title": "Curated Debloater",
        "deb_level": "Level",
        "deb_level_light": "Light (safe)",
        "deb_level_aggressive": "Aggressive (advanced)",
        "deb_action": "Action",
        "deb_action_uninstall": "Uninstall",
        "deb_action_disable": "Disable",
        "deb_select_all": "Select all",
        "deb_clear": "Clear",
        "deb_dry_run": "Dry run",
        "deb_run": "Run",
        "deb_nothing_selected": "Nothing to do",
        "deb_nothing_selected_msg": "No packages selected.",
        "deb_warn_blacklist": "Blacklisted packages cannot be selected.",

        # Preview
        "prev_title": "Preview operations",
        "prev_subtitle": "{n} operation(s) will be {action}ed on device {serial}.",
        "prev_commands": "Commands that will be executed:",
        "prev_warning_title": "WARNING",
        "prev_warning_body": (
            "This operation will MODIFY your device. Removing the wrong package "
            "can cause bootloops, loss of features, or require a factory reset. "
            "A backup will be created automatically. Proceed only if you have "
            "read the package descriptions and understand the risks."
        ),
        "prev_dry_run_note": "Dry run is ENABLED: no changes will be made.",
        "prev_ack": "I have read the warnings and understand the risks.",
        "prev_cancel": "Cancel",
        "prev_confirm": "Execute",

        # Results
        "res_title": "Batch results",
        "res_close": "Close",

        # Packages
        "pkg_title": "All Installed Packages",
        "pkg_search": "Search...",
        "pkg_filter_all": "All",
        "pkg_filter_enabled": "Enabled",
        "pkg_filter_disabled": "Disabled",
        "pkg_load": "Load packages",
        "pkg_no_device": "Connect a device to list packages.",
        "pkg_force_off_msg": "Only curated packages can be selected. Enable force mode in Settings to select any package.",
        "pkg_force_on_msg": "FORCE MODE ENABLED: you can select any package except blacklisted ones.",

        # Backups
        "bak_title": "Backups",
        "bak_refresh": "Refresh list",
        "bak_none": "No backups yet.",
        "bak_restore": "Restore",
        "bak_confirm_title": "Confirm restore",
        "bak_confirm_msg": "Restore {n} package(s) from {name}?",
        "bak_error_read": "Cannot read backup: {msg}",

        # Settings
        "set_title": "Settings",
        "set_language": "Language",
        "set_theme": "Theme",
        "set_theme_dark": "Dark",
        "set_theme_light": "Light",
        "set_force_mode": "Force mode (advanced)",
        "set_force_mode_warn": (
            "Force mode lets you uninstall packages that are not in the "
            "curated lists. This is EXTREMELY DANGEROUS and can brick your "
            "device. Enable only if you know exactly what you are doing."
        ),
        "set_force_enable_confirm": (
            "You are about to enable FORCE MODE.\n\n"
            "This allows removal of system packages outside the curated lists. "
            "Removing the wrong package can BRICK your device permanently.\n\n"
            "Are you absolutely sure?"
        ),
        "set_force_second_confirm": (
            "Last confirmation.\n\n"
            "By enabling force mode you accept full responsibility for any "
            "damage to your device.\n\n"
            "Enable force mode?"
        ),
        "set_saved": "Settings saved.",
        "set_about": "About",
        "set_about_body": (
            "OPlus Toolkit v0.1.0\n"
            "Supports ColorOS, OxygenOS, Realme UI (Android 16 era).\n"
            "Blacklisted packages are always blocked."
        ),
        "set_apply": "Apply",
    },

    "it": {
        # App
        "app_title": "OPlus Toolkit",
        "app_subtitle": "Debloater per ColorOS, OxygenOS e Realme UI",

        # Sidebar
        "nav_dashboard": "Dashboard",
        "nav_debloater": "Debloater",
        "nav_packages": "Tutti i pacchetti",
        "nav_backups": "Backup",
        "nav_settings": "Impostazioni",

        # Status
        "status_ready": "Pronto.",
        "status_scanning": "Scansione dispositivo...",
        "status_no_device": "Nessun dispositivo collegato.",
        "status_adb_missing": "ADB non trovato nel PATH.",
        "status_connected": "Connesso a {model}",
        "status_backup_saved": "Backup salvato: {name}",
        "status_processing": "Elaborazione {i}/{n}...",
        "status_error": "Errore: {msg}",
        "status_adb_restarted": "Server ADB riavviato.",
        "status_loaded_packages": "Caricati {n} pacchetti.",

        # Dashboard
        "dash_title": "Dashboard dispositivo",
        "dash_refresh": "Aggiorna info dispositivo",
        "dash_restart_adb": "Riavvia server ADB",
        "dash_no_device": "Nessun dispositivo collegato.\nCollega un dispositivo via USB e abilita il debug USB.",
        "dash_adb_missing": "ADB non installato.",

        # Debloater
        "deb_title": "Debloater curato",
        "deb_level": "Livello",
        "deb_level_light": "Light (sicuro)",
        "deb_level_aggressive": "Aggressive (avanzato)",
        "deb_action": "Azione",
        "deb_action_uninstall": "Disinstalla",
        "deb_action_disable": "Disabilita",
        "deb_select_all": "Seleziona tutto",
        "deb_clear": "Pulisci",
        "deb_dry_run": "Dry run",
        "deb_run": "Esegui",
        "deb_nothing_selected": "Niente da fare",
        "deb_nothing_selected_msg": "Nessun pacchetto selezionato.",
        "deb_warn_blacklist": "I pacchetti in blacklist non sono selezionabili.",

        # Preview
        "prev_title": "Anteprima operazioni",
        "prev_subtitle": "{n} operazione(i) di tipo '{action}' sul dispositivo {serial}.",
        "prev_commands": "Comandi che verranno eseguiti:",
        "prev_warning_title": "ATTENZIONE",
        "prev_warning_body": (
            "Questa operazione MODIFICHERÀ il tuo dispositivo. Rimuovere il "
            "pacchetto sbagliato può causare bootloop, perdita di funzionalità "
            "o richiedere un ripristino di fabbrica. Verrà creato un backup "
            "automatico. Procedi solo se hai letto le descrizioni e compreso i rischi."
        ),
        "prev_dry_run_note": "Dry run ATTIVO: nessuna modifica verrà effettuata.",
        "prev_ack": "Ho letto gli avvisi e comprendo i rischi.",
        "prev_cancel": "Annulla",
        "prev_confirm": "Esegui",

        # Results
        "res_title": "Risultati batch",
        "res_close": "Chiudi",

        # Packages
        "pkg_title": "Tutti i pacchetti installati",
        "pkg_search": "Cerca...",
        "pkg_filter_all": "Tutti",
        "pkg_filter_enabled": "Attivi",
        "pkg_filter_disabled": "Disabilitati",
        "pkg_load": "Carica pacchetti",
        "pkg_no_device": "Collega un dispositivo per elencare i pacchetti.",
        "pkg_force_off_msg": "Puoi selezionare solo i pacchetti curati. Attiva la force mode nelle Impostazioni per selezionare qualsiasi pacchetto.",
        "pkg_force_on_msg": "FORCE MODE ATTIVA: puoi selezionare qualsiasi pacchetto tranne quelli in blacklist.",

        # Backups
        "bak_title": "Backup",
        "bak_refresh": "Aggiorna elenco",
        "bak_none": "Nessun backup presente.",
        "bak_restore": "Ripristina",
        "bak_confirm_title": "Conferma ripristino",
        "bak_confirm_msg": "Ripristinare {n} pacchetto(i) da {name}?",
        "bak_error_read": "Impossibile leggere il backup: {msg}",

        # Settings
        "set_title": "Impostazioni",
        "set_language": "Lingua",
        "set_theme": "Tema",
        "set_theme_dark": "Scuro",
        "set_theme_light": "Chiaro",
        "set_force_mode": "Force mode (avanzata)",
        "set_force_mode_warn": (
            "La force mode permette di disinstallare pacchetti che non sono "
            "nelle liste curate. È ESTREMAMENTE PERICOLOSO e può brickare il "
            "dispositivo. Attivala solo se sai esattamente cosa stai facendo."
        ),
        "set_force_enable_confirm": (
            "Stai per attivare la FORCE MODE.\n\n"
            "Questo consente la rimozione di pacchetti di sistema fuori dalle "
            "liste curate. Rimuovere il pacchetto sbagliato può BRICKARE il "
            "dispositivo in modo permanente.\n\n"
            "Sei assolutamente sicuro?"
        ),
        "set_force_second_confirm": (
            "Ultima conferma.\n\n"
            "Attivando la force mode accetti ogni responsabilità per eventuali "
            "danni al dispositivo.\n\n"
            "Attivare la force mode?"
        ),
        "set_saved": "Impostazioni salvate.",
        "set_about": "Informazioni",
        "set_about_body": (
            "OPlus Toolkit v0.1.0\n"
            "Supporta ColorOS, OxygenOS, Realme UI (era Android 16).\n"
            "I pacchetti in blacklist sono sempre bloccati."
        ),
        "set_apply": "Applica",
    },
}
