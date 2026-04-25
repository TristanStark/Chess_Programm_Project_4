import customtkinter as ctk


class ExportReportPopup(ctk.CTkToplevel):
    def __init__(self, parent, report_options, on_export_callback):
        super().__init__(parent)
        self.report_options = list(report_options)
        self.on_export_callback = on_export_callback

        self.title("Export Report")
        self.geometry("760x190")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Select the report to generate",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")

        labels = [option.label for option in self.report_options]
        self._selected_report_label = ctk.StringVar(value=(labels[0] if labels else ""))

        self.report_option_menu = ctk.CTkOptionMenu(
            self,
            variable=self._selected_report_label,
            values=labels or ["No report available"],
        )
        self.report_option_menu.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.error_label = ctk.CTkLabel(self, text="", text_color="#B00020", anchor="w")
        self.error_label.grid(row=2, column=0, padx=12, pady=(0, 4), sticky="ew")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(actions, text="Export", command=self._on_export).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Cancel", command=self.destroy).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        self.bind("<Escape>", lambda _event: self.destroy())

    def _on_export(self):
        selected_label = self._selected_report_label.get().strip()
        option = next(
            (report_option for report_option in self.report_options if report_option.label == selected_label),
            None,
        )
        if option is None:
            self.error_label.configure(text="Invalid report selection.")
            return

        success, message = self.on_export_callback(option)
        if success:
            self.destroy()
            return

        self.error_label.configure(text=message)
