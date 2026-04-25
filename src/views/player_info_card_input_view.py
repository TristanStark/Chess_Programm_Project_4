from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk


class PlayerInfoCardInput(CtkLabelFrame):
    def __init__(
        self,
        parent,
        first_name="",
        last_name="",
        date_of_birth="",
        ncid="",
        **kwargs,
    ):
        super().__init__(parent, text="Player Info:", **kwargs)

        self.content.grid_columnconfigure(0, weight=0)
        self.content.grid_columnconfigure(1, weight=0)
        self.content.grid_columnconfigure(2, weight=1)

        self._build_ui()
        self.set_player_info(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            ncid=ncid,
        )

    def _build_ui(self):
        row = 0

        ctk.CTkLabel(self.content, text="First Name", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.first_name_entry = ctk.CTkEntry(self.content)
        self.first_name_entry.grid(row=row, column=2, sticky="ew", pady=4)

        row += 1
        ctk.CTkLabel(self.content, text="Last Name", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.last_name_entry = ctk.CTkEntry(self.content)
        self.last_name_entry.grid(row=row, column=2, sticky="ew", pady=4)

        row += 1
        ctk.CTkLabel(self.content, text="Date of Birth", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.dob_entry = ctk.CTkEntry(self.content, placeholder_text="YYYY-MM-DD")
        self.dob_entry.grid(row=row, column=2, sticky="ew", pady=4)

        row += 1
        ctk.CTkLabel(self.content, text="NCID", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ctk.CTkLabel(self.content, text=":", width=10, anchor="center").grid(
            row=row, column=1, sticky="w", padx=(0, 8), pady=4
        )
        self.ncid_entry = ctk.CTkEntry(self.content, placeholder_text="AA12345")
        self.ncid_entry.grid(row=row, column=2, sticky="ew", pady=4)

    def set_player_info(self, first_name="", last_name="", date_of_birth="", ncid=""):
        self.clear()
        self.first_name_entry.insert(0, first_name)
        self.last_name_entry.insert(0, last_name)
        self.dob_entry.insert(0, date_of_birth)
        self.ncid_entry.insert(0, ncid)

    def get_player_info(self):
        return {
            "first_name": self.first_name_entry.get().strip(),
            "last_name": self.last_name_entry.get().strip(),
            "date_of_birth": self.dob_entry.get().strip(),
            "ncid": self.ncid_entry.get().strip(),
        }

    def clear(self):
        self.first_name_entry.delete(0, "end")
        self.last_name_entry.delete(0, "end")
        self.dob_entry.delete(0, "end")
        self.ncid_entry.delete(0, "end")
