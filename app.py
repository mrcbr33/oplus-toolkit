"""
app.py - OPlus Toolkit GUI (CustomTkinter).

Material-inspired layout with sidebar navigation, bilingual UI (EN/IT),
mandatory command preview before execution, automatic backups, and a
persistent log panel.
"""

from __future__ import annotations

import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from config import load_config, save_config
from core import (
    Action,
    BatchResult,
    OperationResult,
    list_disabled_packages,
    list_installed_packages,
    process_batch,
    restore_from_backup,
)
from i18n import I18N
from utils import (
    create_backup,
    format_package_display,
    get_device_info,
    get_packages_by_level,
    get_ready_devices,
    is_adb_available,
    list_backups,
    load_backup,
    load_bloatware_lists,
    setup_logger,
)


# ============================================================
# THEME
# ============================================================

ctk.set_default_color_theme("blue")

BG_APP = "#0f1317"
BG_SIDEBAR = "#171c22"
BG_CARD = "#1f262d"
BG_CARD_ALT = "#252d35"
BG_HOVER = "#2c353f"
BG_INPUT = "#1a2028"
FG_PRIMARY = "#f5f7fa"
FG_SECONDARY = "#98a2ad"
FG_MUTED = "#5d6874"
ACCENT = "#3b82f6"
ACCENT_HOVER = "#2563eb"
DANGER = "#ef4444"
DANGER_HOVER = "#dc2626"
WARNING = "#f59e0b"
SUCCESS = "#10b981"

FONT_H1 = ("Segoe UI", 22, "bold")
FONT_H2 = ("Segoe UI", 16, "bold")
FONT_H3 = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 11)
FONT_NAV = ("Segoe UI", 12, "bold")


# ============================================================
# DIALOGS
# ============================================================

class PreviewDialog(ctk.CTkToplevel):
    """Shows the ADB commands that will be executed and requires acknowledgement."""

    def __init__(
        self,
        parent,
        t: dict,
        action: Action,
        packages: list[str],
        serial: str,
        dry_run: bool,
        on_confirm: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.t = t
        self.on_confirm = on_confirm
        self._packages = packages
        self._action = action
        self._serial = serial
        self._dry_run = dry_run

        self.title(t["prev_title"])
        self.geometry("780x700")
        self.minsize(640, 520)
        self.configure(fg_color=BG_APP)

        # Build widgets after the window is mapped, to avoid rendering issues
        # on Wayland / Hyprland / some CTk versions.
        self.after(80, self._build)

    def _build(self) -> None:
        t = self.t
        action = self._action
        packages = self._packages
        serial = self._serial
        dry_run = self._dry_run

        # Title
        ctk.CTkLabel(
            self, text=t["prev_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", padx=25, pady=(20, 4))

        # Subtitle
        ctk.CTkLabel(
            self,
            text=t["prev_subtitle"].format(
                n=len(packages), action=action.value, serial=serial or "?"
            ),
            font=FONT_BODY,
            text_color=FG_SECONDARY,
        ).pack(anchor="w", padx=25, pady=(0, 12))

        # Warning banner
        if dry_run:
            banner_bg = "#1e3a5f"
            banner_fg = ACCENT
            banner_text = t["prev_dry_run_note"]
            banner_icon = "i"
        else:
            banner_bg = "#3a1e1e"
            banner_fg = DANGER
            banner_text = t["prev_warning_body"]
            banner_icon = "!"

        banner = ctk.CTkFrame(self, fg_color=banner_bg, corner_radius=10)
        banner.pack(fill="x", padx=25, pady=(0, 12))

        ctk.CTkLabel(
            banner,
            text=f"[ {banner_icon} ]  {t['prev_warning_title']}",
            font=FONT_H3,
            text_color=banner_fg,
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            banner,
            text=banner_text,
            font=FONT_BODY,
            text_color=FG_PRIMARY,
            wraplength=680,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=15, pady=(0, 12))

        # Commands label
        ctk.CTkLabel(
            self,
            text=t["prev_commands"],
            font=FONT_H3,
            text_color=FG_SECONDARY,
        ).pack(anchor="w", padx=25, pady=(4, 4))

        # Commands box
        verb_map = {
            Action.UNINSTALL: "uninstall --user 0",
            Action.DISABLE: "disable-user --user 0",
            Action.ENABLE: "enable --user 0",
            Action.RESTORE: "install-existing --user 0",
        }
        verb = verb_map.get(action, action.value)
        commands = "\n".join(f"adb shell pm {verb} {pkg}" for pkg in packages)

        cmd_box = ctk.CTkTextbox(
            self,
            font=FONT_MONO,
            fg_color=BG_INPUT,
            text_color=FG_PRIMARY,
            border_color=BG_CARD_ALT,
            border_width=1,
            wrap="word",
            height=220,
        )
        cmd_box.pack(fill="both", expand=True, padx=25, pady=(0, 12))
        cmd_box.insert("1.0", commands)
        cmd_box.configure(state="disabled")

        # Acknowledgement checkbox
        self.ack_var = tk.BooleanVar(value=False)
        ack = ctk.CTkCheckBox(
            self,
            text=t["prev_ack"],
            variable=self.ack_var,
            font=FONT_BODY,
            text_color=FG_PRIMARY,
            command=self._toggle_confirm,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            checkmark_color=FG_PRIMARY,
        )
        ack.pack(anchor="w", padx=25, pady=(0, 12))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_row,
            text=t["prev_cancel"],
            command=self.destroy,
            fg_color=BG_CARD_ALT,
            hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            height=38,
            width=120,
            corner_radius=8,
        ).pack(side="right", padx=(10, 0))

        self.confirm_btn = ctk.CTkButton(
            btn_row,
            text=t["prev_confirm"],
            command=self._confirm,
            fg_color=DANGER if not dry_run else ACCENT,
            hover_color=DANGER_HOVER if not dry_run else ACCENT_HOVER,
            text_color=FG_PRIMARY,
            height=38,
            width=140,
            corner_radius=8,
            state="disabled",
        )
        self.confirm_btn.pack(side="right")

        # After layout is done, take focus
        self.after(120, self._post_build)

    def _post_build(self) -> None:
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _toggle_confirm(self) -> None:
        self.confirm_btn.configure(
            state="normal" if self.ack_var.get() else "disabled"
        )

    def _confirm(self) -> None:
        self.destroy()
        self.on_confirm()


class ResultsDialog(ctk.CTkToplevel):
    """Shows batch operation results."""

    def __init__(self, parent, t: dict, result: BatchResult) -> None:
        super().__init__(parent)
        self.t = t
        self._result = result

        self.title(t["res_title"])
        self.geometry("780x540")
        self.minsize(600, 400)
        self.configure(fg_color=BG_APP)

        self.after(80, self._build)

    def _build(self) -> None:
        t = self.t
        result = self._result

        # Header
        ctk.CTkLabel(
            self, text=t["res_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", padx=25, pady=(20, 4))

        summary_color = SUCCESS if result.failed == 0 else WARNING
        ctk.CTkLabel(
            self,
            text=result.summary(),
            font=FONT_BODY,
            text_color=summary_color,
        ).pack(anchor="w", padx=25, pady=(0, 12))

        # Results
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_CARD, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        for res in result.results:
            color = SUCCESS if res.success else DANGER
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row, text="●", font=FONT_BODY, text_color=color, width=20
            ).pack(side="left", padx=(6, 6))

            ctk.CTkLabel(
                row,
                text=f"{res.action.value} {res.package}",
                font=FONT_MONO,
                text_color=FG_PRIMARY,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                row,
                text=res.message[:80] + ("..." if len(res.message) > 80 else ""),
                font=FONT_SMALL,
                text_color=FG_SECONDARY,
                anchor="e",
            ).pack(side="right", padx=8)

        # Close
        ctk.CTkButton(
            self,
            text=t["res_close"],
            command=self.destroy,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=FG_PRIMARY,
            height=38,
            width=120,
            corner_radius=8,
        ).pack(pady=(0, 20))

        self.after(120, self._post_build)

    def _post_build(self) -> None:
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass


# ============================================================
# BASE SECTION
# ============================================================

class BaseSection(ctk.CTkFrame):
    def __init__(self, parent, app: "OPlusToolkitApp") -> None:
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.t = app.t
        self.build()

    def build(self) -> None:
        pass

    def on_show(self) -> None:
        pass

    def refresh_texts(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        self.t = self.app.t
        self.build()


# ============================================================
# DASHBOARD SECTION
# ============================================================

class DashboardSection(BaseSection):
    def build(self) -> None:
        t = self.t
        ctk.CTkLabel(
            self, text=t["dash_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill="x", pady=(0, 15))

        self.device_label = ctk.CTkLabel(
            card,
            text=t["status_scanning"],
            font=FONT_BODY,
            text_color=FG_PRIMARY,
            justify="left",
            anchor="w",
        )
        self.device_label.pack(fill="x", padx=25, pady=25)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkButton(
            row,
            text=t["dash_refresh"],
            command=self.app.refresh_device_info,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=FG_PRIMARY,
            height=38,
            corner_radius=8,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            row,
            text=t["dash_restart_adb"],
            command=self.app.restart_adb,
            fg_color=BG_CARD_ALT,
            hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            height=38,
            corner_radius=8,
        ).pack(side="left")

    def on_show(self) -> None:
        self.app.refresh_device_info()


# ============================================================
# DEBLOATER SECTION
# ============================================================

class DebloaterSection(BaseSection):
    def build(self) -> None:
        t = self.t

        ctk.CTkLabel(
            self, text=t["deb_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        controls = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        controls.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(controls, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            inner, text=t["deb_level"], font=FONT_H3, text_color=FG_SECONDARY
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        level_display = {
            t["deb_level_light"]: "light",
            t["deb_level_aggressive"]: "aggressive",
        }
        self.level_reverse = {v: k for k, v in level_display.items()}
        self.level_var = tk.StringVar(
            value=self.level_reverse.get(
                self.app.config["last_level"], t["deb_level_light"]
            )
        )
        ctk.CTkOptionMenu(
            inner,
            values=list(level_display.keys()),
            variable=self.level_var,
            command=lambda _: self._on_level_change(),
            fg_color=BG_INPUT,
            button_color=BG_CARD_ALT,
            button_hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            dropdown_fg_color=BG_CARD_ALT,
            width=200,
        ).grid(row=0, column=1, padx=(0, 25), sticky="w")

        ctk.CTkLabel(
            inner, text=t["deb_action"], font=FONT_H3, text_color=FG_SECONDARY
        ).grid(row=0, column=2, padx=(0, 8), sticky="w")

        action_display = {
            t["deb_action_uninstall"]: "uninstall",
            t["deb_action_disable"]: "disable",
        }
        self.action_reverse = {v: k for k, v in action_display.items()}
        self.action_var = tk.StringVar(
            value=self.action_reverse.get(
                self.app.config["last_action"], t["deb_action_uninstall"]
            )
        )
        ctk.CTkOptionMenu(
            inner,
            values=list(action_display.keys()),
            variable=self.action_var,
            command=lambda _: self._on_action_change(),
            fg_color=BG_INPUT,
            button_color=BG_CARD_ALT,
            button_hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            dropdown_fg_color=BG_CARD_ALT,
            width=160,
        ).grid(row=0, column=3, padx=(0, 25), sticky="w")

        ctk.CTkButton(
            inner,
            text=t["deb_select_all"],
            command=self._select_all,
            fg_color=BG_CARD_ALT,
            hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            height=34,
            width=130,
            corner_radius=8,
        ).grid(row=0, column=4, padx=(0, 8))

        ctk.CTkButton(
            inner,
            text=t["deb_clear"],
            command=self._clear_all,
            fg_color=BG_CARD_ALT,
            hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            height=34,
            width=90,
            corner_radius=8,
        ).grid(row=0, column=5, padx=(0, 25))

        self.dry_run_var = tk.BooleanVar(value=self.app.config["dry_run"])
        ctk.CTkSwitch(
            inner,
            text=t["deb_dry_run"],
            variable=self.dry_run_var,
            command=self._on_dry_run_change,
            font=FONT_H3,
            text_color=FG_PRIMARY,
            progress_color=ACCENT,
        ).grid(row=0, column=6, sticky="e")

        inner.grid_columnconfigure(7, weight=1)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_CARD, corner_radius=12, height=280
        )
        self.scroll.pack(fill="both", expand=True, pady=(0, 15))

        self.package_vars: dict[str, tk.BooleanVar] = {}
        self.package_boxes: dict[str, ctk.CTkCheckBox] = {}

        self._populate_packages()

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x")

        self.progress = ctk.CTkProgressBar(
            bottom, height=8, corner_radius=4, progress_color=ACCENT
        )
        self.progress.set(0)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 15))

        ctk.CTkButton(
            bottom,
            text=t["deb_run"],
            command=self._run,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=FG_PRIMARY,
            height=42,
            width=160,
            corner_radius=8,
            font=FONT_H3,
        ).pack(side="right")

    def _on_level_change(self) -> None:
        self.app.config["last_level"] = self._current_level()
        save_config(self.app.config)
        self._populate_packages()

    def _on_action_change(self) -> None:
        self.app.config["last_action"] = self._current_action()
        save_config(self.app.config)

    def _on_dry_run_change(self) -> None:
        self.app.config["dry_run"] = bool(self.dry_run_var.get())
        save_config(self.app.config)

    def _current_level(self) -> str:
        return self.level_reverse.get(self.level_var.get(), "light")

    def _current_action(self) -> str:
        return self.action_reverse.get(self.action_var.get(), "uninstall")

    def _populate_packages(self) -> None:
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.package_vars.clear()
        self.package_boxes.clear()

        level = self._current_level()
        packages = get_packages_by_level(self.app.bloatware, level)

        if not packages:
            ctk.CTkLabel(
                self.scroll, text="—", font=FONT_BODY, text_color=FG_MUTED
            ).pack(pady=20)
            return

        for pkg in packages:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=3, padx=5)

            var = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                row,
                text=format_package_display(pkg),
                variable=var,
                font=FONT_BODY,
                text_color=FG_PRIMARY,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                checkmark_color=FG_PRIMARY,
            )
            cb.pack(side="left", padx=5)

            ctk.CTkLabel(
                row,
                text=pkg.get("reason", ""),
                font=FONT_SMALL,
                text_color=FG_SECONDARY,
                anchor="e",
                justify="right",
                wraplength=420,
            ).pack(side="right", padx=8)

            self.package_vars[pkg["package"]] = var
            self.package_boxes[pkg["package"]] = cb

    def _select_all(self) -> None:
        for var in self.package_vars.values():
            var.set(True)

    def _clear_all(self) -> None:
        for var in self.package_vars.values():
            var.set(False)

    def _get_selected(self) -> list[str]:
        return [pkg for pkg, var in self.package_vars.items() if var.get()]

    def _run(self) -> None:
        selected = self._get_selected()
        if not selected:
            messagebox.showinfo(
                self.t["deb_nothing_selected"], self.t["deb_nothing_selected_msg"]
            )
            return

        action = Action(self._current_action())
        dry_run = bool(self.dry_run_var.get())
        serial = self.app.device_info.get("serial", "") or ""

        def on_confirm() -> None:
            self._execute(selected, action, dry_run, serial)

        PreviewDialog(
            self.app,
            self.t,
            action=action,
            packages=selected,
            serial=serial,
            dry_run=dry_run,
            on_confirm=on_confirm,
        )

    def _execute(
        self, packages: list[str], action: Action, dry_run: bool, serial: str
    ) -> None:
        if not dry_run:
            try:
                backup_path = create_backup(
                    packages, self.app.device_info, action.value
                )
                self.app.set_status(
                    self.t["status_backup_saved"].format(name=backup_path.name)
                )
            except Exception as exc:
                self.app.set_status(
                    self.t["status_error"].format(msg=str(exc)), error=True
                )
                return

        self.progress.set(0)

        def on_progress(index: int, total: int, _res: OperationResult) -> None:
            self.progress.set(index / total)
            self.app.set_status(
                self.t["status_processing"].format(i=index, n=total)
            )

        def worker() -> None:
            try:
                result = process_batch(
                    packages=packages,
                    action=action,
                    serial=serial or None,
                    dry_run=dry_run,
                    progress_callback=on_progress,
                )
            except Exception as exc:
                self.app.set_status(
                    self.t["status_error"].format(msg=str(exc)), error=True
                )
                return

            self.app.set_status(result.summary())
            self.app.log_result(result)
            self.after(0, lambda: ResultsDialog(self.app, self.t, result))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================
# ALL PACKAGES SECTION
# ============================================================

class PackagesSection(BaseSection):
    def build(self) -> None:
        t = self.t

        ctk.CTkLabel(
            self, text=t["pkg_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        force_on = bool(self.app.config.get("force_mode", False))
        if force_on:
            banner_bg = "#3a1e1e"
            banner_fg = DANGER
            banner_text = t["pkg_force_on_msg"]
        else:
            banner_bg = BG_CARD
            banner_fg = FG_SECONDARY
            banner_text = t["pkg_force_off_msg"]

        banner = ctk.CTkFrame(self, fg_color=banner_bg, corner_radius=10)
        banner.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(
            banner,
            text=banner_text,
            font=FONT_SMALL,
            text_color=banner_fg,
            wraplength=900,
            justify="left",
        ).pack(padx=15, pady=10, anchor="w")

        bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        bar.pack(fill="x", pady=(0, 15))

        bar_inner = ctk.CTkFrame(bar, fg_color="transparent")
        bar_inner.pack(fill="x", padx=20, pady=12)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._render_packages())

        ctk.CTkEntry(
            bar_inner,
            textvariable=self.search_var,
            placeholder_text=t["pkg_search"],
            fg_color=BG_INPUT,
            text_color=FG_PRIMARY,
            border_color=BG_CARD_ALT,
            height=36,
            width=300,
        ).pack(side="left", padx=(0, 15))

        self.filter_var = tk.StringVar(value=t["pkg_filter_all"])
        ctk.CTkOptionMenu(
            bar_inner,
            values=[
                t["pkg_filter_all"],
                t["pkg_filter_enabled"],
                t["pkg_filter_disabled"],
            ],
            variable=self.filter_var,
            command=lambda _: self._render_packages(),
            fg_color=BG_INPUT,
            button_color=BG_CARD_ALT,
            button_hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            dropdown_fg_color=BG_CARD_ALT,
            width=160,
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            bar_inner,
            text=t["pkg_load"],
            command=self._load_packages,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=FG_PRIMARY,
            height=36,
            width=160,
            corner_radius=8,
        ).pack(side="left")

        ctk.CTkButton(
            bar_inner,
            text=t["deb_run"],
            command=self._run,
            fg_color=DANGER if force_on else BG_CARD_ALT,
            hover_color=DANGER_HOVER if force_on else BG_HOVER,
            text_color=FG_PRIMARY,
            height=36,
            width=120,
            corner_radius=8,
        ).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_CARD, corner_radius=12)
        self.scroll.pack(fill="both", expand=True, pady=(0, 10))

        self.package_vars: dict[str, tk.BooleanVar] = {}
        self.all_packages: list[str] = []
        self.enabled_packages: set[str] = set()

        ctk.CTkLabel(
            self.scroll,
            text=t["pkg_no_device"],
            font=FONT_BODY,
            text_color=FG_MUTED,
        ).pack(pady=20)

    def on_show(self) -> None:
        if not self.all_packages and get_ready_devices():
            self._load_packages()

    def _load_packages(self) -> None:
        if not get_ready_devices():
            messagebox.showinfo(self.t["pkg_title"], self.t["pkg_no_device"])
            return

        self.app.set_status(self.t["status_scanning"])

        def worker() -> None:
            try:
                installed = list_installed_packages()
                disabled = list_disabled_packages()
            except Exception as exc:
                self.app.set_status(
                    self.t["status_error"].format(msg=str(exc)), error=True
                )
                return

            enabled_set = set(installed)
            all_pkgs = sorted(set(installed) | set(disabled))

            self.all_packages = all_pkgs
            self.enabled_packages = enabled_set
            self.app.set_status(
                self.t["status_loaded_packages"].format(n=len(all_pkgs))
            )
            self.after(0, self._render_packages)

        threading.Thread(target=worker, daemon=True).start()

    def _render_packages(self) -> None:
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.package_vars.clear()

        if not self.all_packages:
            ctk.CTkLabel(
                self.scroll,
                text=self.t["pkg_no_device"],
                font=FONT_BODY,
                text_color=FG_MUTED,
            ).pack(pady=20)
            return

        query = self.search_var.get().lower().strip()
        filter_mode = self.filter_var.get()

        force_on = bool(self.app.config.get("force_mode", False))
        blacklist = {
            p["package"]
            for p in get_packages_by_level(self.app.bloatware, "blacklist")
        }
        curated = {
            p["package"]
            for lvl in ("light", "aggressive")
            for p in get_packages_by_level(self.app.bloatware, lvl)
        }

        shown = 0
        for pkg in self.all_packages:
            if query and query not in pkg.lower():
                continue

            is_enabled = pkg in self.enabled_packages
            if filter_mode == self.t["pkg_filter_enabled"] and not is_enabled:
                continue
            if filter_mode == self.t["pkg_filter_disabled"] and is_enabled:
                continue

            blacklisted = pkg in blacklist
            selectable = (pkg in curated) or (force_on and not blacklisted)

            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2, padx=5)

            var = tk.BooleanVar(value=False)
            state = "normal" if selectable else "disabled"
            cb = ctk.CTkCheckBox(
                row,
                text=pkg,
                variable=var,
                font=FONT_MONO,
                text_color=FG_PRIMARY if selectable else FG_MUTED,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                checkmark_color=FG_PRIMARY,
                state=state,
            )
            cb.pack(side="left", padx=5)

            if blacklisted:
                tag = "BLACKLIST"
                tag_color = DANGER
            elif pkg in curated:
                tag = "CURATED"
                tag_color = SUCCESS
            elif force_on:
                tag = "FORCE"
                tag_color = WARNING
            else:
                tag = ""
                tag_color = FG_MUTED

            if tag:
                ctk.CTkLabel(
                    row, text=tag, font=FONT_SMALL, text_color=tag_color
                ).pack(side="right", padx=8)

            if not is_enabled:
                ctk.CTkLabel(
                    row,
                    text="disabled",
                    font=FONT_SMALL,
                    text_color=FG_MUTED,
                ).pack(side="right", padx=8)

            self.package_vars[pkg] = var
            shown += 1

        if shown == 0:
            ctk.CTkLabel(
                self.scroll, text="—", font=FONT_BODY, text_color=FG_MUTED
            ).pack(pady=20)

    def _get_selected(self) -> list[str]:
        return [pkg for pkg, var in self.package_vars.items() if var.get()]

    def _run(self) -> None:
        selected = self._get_selected()
        if not selected:
            messagebox.showinfo(
                self.t["deb_nothing_selected"], self.t["deb_nothing_selected_msg"]
            )
            return

        force_on = bool(self.app.config.get("force_mode", False))
        if not force_on:
            messagebox.showinfo(self.t["pkg_title"], self.t["pkg_force_off_msg"])
            return

        action = Action(self._current_action())
        dry_run = bool(self.app.config.get("dry_run", True))
        serial = self.app.device_info.get("serial", "") or ""

        def on_confirm() -> None:
            self._execute(selected, action, dry_run, serial)

        PreviewDialog(
            self.app,
            self.t,
            action=action,
            packages=selected,
            serial=serial,
            dry_run=dry_run,
            on_confirm=on_confirm,
        )

    def _current_action(self) -> str:
        return self.app.config.get("last_action", "uninstall")

    def _execute(
        self, packages: list[str], action: Action, dry_run: bool, serial: str
    ) -> None:
        if not dry_run:
            try:
                create_backup(packages, self.app.device_info, action.value)
            except Exception as exc:
                self.app.set_status(
                    self.t["status_error"].format(msg=str(exc)), error=True
                )
                return

        def worker() -> None:
            try:
                result = process_batch(
                    packages=packages,
                    action=action,
                    serial=serial or None,
                    dry_run=dry_run,
                )
            except Exception as exc:
                self.app.set_status(
                    self.t["status_error"].format(msg=str(exc)), error=True
                )
                return

            self.app.set_status(result.summary())
            self.app.log_result(result)
            self.after(0, lambda: ResultsDialog(self.app, self.t, result))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================
# BACKUPS SECTION
# ============================================================

class BackupsSection(BaseSection):
    def build(self) -> None:
        t = self.t

        ctk.CTkLabel(
            self, text=t["bak_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        ctk.CTkButton(
            self,
            text=t["bak_refresh"],
            command=self._populate,
            fg_color=BG_CARD_ALT,
            hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            height=36,
            width=160,
            corner_radius=8,
        ).pack(anchor="w", pady=(0, 15))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_CARD, corner_radius=12)
        self.scroll.pack(fill="both", expand=True)

        self._populate()

    def on_show(self) -> None:
        self._populate()

    def _populate(self) -> None:
        for widget in self.scroll.winfo_children():
            widget.destroy()

        backups = list_backups()
        if not backups:
            ctk.CTkLabel(
                self.scroll,
                text=self.t["bak_none"],
                font=FONT_BODY,
                text_color=FG_MUTED,
            ).pack(pady=20)
            return

        for path in backups:
            row = ctk.CTkFrame(self.scroll, fg_color=BG_CARD_ALT, corner_radius=8)
            row.pack(fill="x", pady=4, padx=5)

            ctk.CTkLabel(
                row,
                text=path.name,
                font=FONT_MONO,
                text_color=FG_PRIMARY,
                anchor="w",
            ).pack(side="left", padx=12, pady=10)

            ctk.CTkButton(
                row,
                text=self.t["bak_restore"],
                command=lambda p=path: self._restore(p),
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                text_color=FG_PRIMARY,
                height=30,
                width=110,
                corner_radius=6,
            ).pack(side="right", padx=12, pady=8)

    def _restore(self, path: Path) -> None:
        try:
            data = load_backup(path)
        except Exception as exc:
            messagebox.showerror(
                self.t["bak_title"],
                self.t["bak_error_read"].format(msg=str(exc)),
            )
            return

        count = len(data.get("packages", []))
        if not messagebox.askyesno(
            self.t["bak_confirm_title"],
            self.t["bak_confirm_msg"].format(n=count, name=path.name),
        ):
            return

        def worker() -> None:
            try:
                result = restore_from_backup(data, dry_run=False)
            except Exception as exc:
                self.app.set_status(
                    self.t["status_error"].format(msg=str(exc)), error=True
                )
                return
            self.app.set_status(result.summary())
            self.app.log_result(result)
            self.after(0, lambda: ResultsDialog(self.app, self.t, result))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================
# SETTINGS SECTION
# ============================================================

class SettingsSection(BaseSection):
    def build(self) -> None:
        t = self.t

        ctk.CTkLabel(
            self, text=t["set_title"], font=FONT_H1, text_color=FG_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        # Language
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=25, pady=18)

        ctk.CTkLabel(
            inner, text=t["set_language"], font=FONT_H3, text_color=FG_PRIMARY
        ).pack(side="left")

        self.lang_var = tk.StringVar(value=self.app.config["language"].upper())
        ctk.CTkOptionMenu(
            inner,
            values=["EN", "IT"],
            variable=self.lang_var,
            command=lambda _: self._change_language(),
            fg_color=BG_INPUT,
            button_color=BG_CARD_ALT,
            button_hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            dropdown_fg_color=BG_CARD_ALT,
            width=120,
        ).pack(side="right")

        # Theme
        card2 = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card2.pack(fill="x", pady=(0, 12))

        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="x", padx=25, pady=18)

        ctk.CTkLabel(
            inner2, text=t["set_theme"], font=FONT_H3, text_color=FG_PRIMARY
        ).pack(side="left")

        self.theme_var = tk.StringVar(
            value=t["set_theme_dark"]
            if self.app.config["theme"] == "dark"
            else t["set_theme_light"]
        )
        ctk.CTkOptionMenu(
            inner2,
            values=[t["set_theme_dark"], t["set_theme_light"]],
            variable=self.theme_var,
            command=lambda _: self._change_theme(),
            fg_color=BG_INPUT,
            button_color=BG_CARD_ALT,
            button_hover_color=BG_HOVER,
            text_color=FG_PRIMARY,
            dropdown_fg_color=BG_CARD_ALT,
            width=150,
        ).pack(side="right")

        # Force mode
        card3 = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card3.pack(fill="x", pady=(0, 12))

        inner3 = ctk.CTkFrame(card3, fg_color="transparent")
        inner3.pack(fill="x", padx=25, pady=18)

        top = ctk.CTkFrame(inner3, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top, text=t["set_force_mode"], font=FONT_H3, text_color=DANGER
        ).pack(side="left")

        self.force_var = tk.BooleanVar(value=bool(self.app.config["force_mode"]))
        ctk.CTkSwitch(
            top,
            text="",
            variable=self.force_var,
            command=self._toggle_force,
            progress_color=DANGER,
        ).pack(side="right")

        ctk.CTkLabel(
            inner3,
            text=t["set_force_mode_warn"],
            font=FONT_SMALL,
            text_color=FG_SECONDARY,
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        # About
        card4 = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        card4.pack(fill="x", pady=(0, 12))

        inner4 = ctk.CTkFrame(card4, fg_color="transparent")
        inner4.pack(fill="x", padx=25, pady=18)

        ctk.CTkLabel(
            inner4, text=t["set_about"], font=FONT_H3, text_color=FG_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner4,
            text=t["set_about_body"],
            font=FONT_SMALL,
            text_color=FG_SECONDARY,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

    def _change_language(self) -> None:
        new_lang = self.lang_var.get().lower()
        if new_lang == self.app.config["language"]:
            return
        self.app.config["language"] = new_lang
        save_config(self.app.config)
        self.app.apply_language()

    def _change_theme(self) -> None:
        new_theme = (
            "dark" if self.theme_var.get() == self.t["set_theme_dark"] else "light"
        )
        self.app.config["theme"] = new_theme
        save_config(self.app.config)
        ctk.set_appearance_mode(new_theme)

    def _toggle_force(self) -> None:
        new_value = bool(self.force_var.get())
        if new_value:
            if not messagebox.askyesno(
                self.t["set_force_mode"], self.t["set_force_enable_confirm"]
            ):
                self.force_var.set(False)
                return
            if not messagebox.askyesno(
                self.t["set_force_mode"], self.t["set_force_second_confirm"]
            ):
                self.force_var.set(False)
                return

        self.app.config["force_mode"] = new_value
        save_config(self.app.config)
        self.app.set_status(self.t["set_saved"])


# ============================================================
# MAIN APP
# ============================================================

class OPlusToolkitApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.config = load_config()
        self.t = I18N[self.config["language"]]

        ctk.set_appearance_mode(self.config["theme"])

        self.title(self.t["app_title"])
        self.geometry(self.config["window_geometry"])
        self.minsize(1000, 640)
        self.configure(fg_color=BG_APP)

        self.logger = setup_logger()
        self.bloatware = load_bloatware_lists()
        self.device_info: dict = {}

        self._build_sidebar()
        self._build_content()
        self._build_status_bar()

        self.sections: dict[str, BaseSection] = {
            "dashboard": DashboardSection(self.content, self),
            "debloater": DebloaterSection(self.content, self),
            "packages": PackagesSection(self.content, self),
            "backups": BackupsSection(self.content, self),
            "settings": SettingsSection(self.content, self),
        }

        self.current_section = ""
        self.show_section("dashboard")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(200, self.refresh_device_info)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self, width=230, corner_radius=0, fg_color=BG_SIDEBAR
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="⚙  " + self.t["app_title"],
            font=FONT_H2,
            text_color=FG_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=22, pady=(24, 4))

        ctk.CTkLabel(
            self.sidebar,
            text=self.t["app_subtitle"],
            font=FONT_SMALL,
            text_color=FG_SECONDARY,
            anchor="w",
            wraplength=190,
            justify="left",
        ).pack(fill="x", padx=22, pady=(0, 24))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        keys = ["dashboard", "debloater", "packages", "backups", "settings"]
        for key in keys:
            btn = ctk.CTkButton(
                self.sidebar,
                text="  " + self.t[f"nav_{key}"],
                font=FONT_NAV,
                anchor="w",
                fg_color="transparent",
                hover_color=BG_HOVER,
                text_color=FG_SECONDARY,
                height=42,
                corner_radius=8,
                command=lambda k=key: self.show_section(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = btn

    def _build_content(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    def _build_status_bar(self) -> None:
        self.status_var = tk.StringVar(value=self.t["status_ready"])
        bar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, height=32, corner_radius=0)
        bar.pack(side="bottom", fill="x")
        ctk.CTkLabel(
            bar,
            textvariable=self.status_var,
            font=FONT_SMALL,
            text_color=FG_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=20)

    def show_section(self, key: str) -> None:
        if key == self.current_section:
            self.sections[key].on_show()
            return

        for sec in self.sections.values():
            sec.pack_forget()

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=BG_CARD, text_color=FG_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=FG_SECONDARY)

        self.sections[key].pack(fill="both", expand=True)
        self.sections[key].on_show()
        self.current_section = key

    def apply_language(self) -> None:
        self.t = I18N[self.config["language"]]
        self.title(self.t["app_title"])

        for key, btn in self.nav_buttons.items():
            btn.configure(text="  " + self.t[f"nav_{key}"])

        for section in self.sections.values():
            section.refresh_texts()

        self.set_status(self.t["status_ready"])

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_var.set(message)
        if error:
            self.logger.error(message)
        else:
            self.logger.info(message)

    def log_result(self, result: BatchResult) -> None:
        self.logger.info(result.summary())
        for res in result.results:
            self.logger.info(str(res))

    def refresh_device_info(self) -> None:
        def worker() -> None:
            if not is_adb_available():
                self.set_status(self.t["status_adb_missing"], error=True)
                self._update_dashboard_label(self.t["dash_adb_missing"])
                return

            devices = get_ready_devices()
            if not devices:
                self.set_status(self.t["status_no_device"])
                self._update_dashboard_label(self.t["dash_no_device"])
                self.device_info = {}
                return

            info = get_device_info()
            self.device_info = info
            text = (
                f"Serial:   {info['serial']}\n"
                f"Brand:    {info['brand']}\n"
                f"Model:    {info['model']}\n"
                f"Android:  {info['android_version']} (SDK {info['sdk_level']})\n"
                f"UI:       {info['ui_type']} {info['ui_version']}"
            )
            self._update_dashboard_label(text)
            self.set_status(self.t["status_connected"].format(model=info["model"]))

        threading.Thread(target=worker, daemon=True).start()

    def _update_dashboard_label(self, text: str) -> None:
        section = self.sections.get("dashboard")
        if isinstance(section, DashboardSection):
            self.after(0, lambda: section.device_label.configure(text=text))

    def restart_adb(self) -> None:
        def worker() -> None:
            subprocess.run(["adb", "kill-server"], capture_output=True)
            subprocess.run(["adb", "start-server"], capture_output=True)
            self.set_status(self.t["status_adb_restarted"])
            self.refresh_device_info()

        threading.Thread(target=worker, daemon=True).start()

    def _on_close(self) -> None:
        self.config["window_geometry"] = self.geometry()
        save_config(self.config)
        self.destroy()


# ============================================================
# ENTRY POINT
# ============================================================

def main() -> None:
    app = OPlusToolkitApp()
    app.mainloop()


if __name__ == "__main__":
    main()