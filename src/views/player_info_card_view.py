from src.views.label_frame import CtkLabelFrame
import customtkinter as ctk


class PlayerInfoCard(CtkLabelFrame):
    def __init__(
        self,
        parent,
        first_name="",
        last_name="",
        date_of_birth="",
        ncid="",
        total_points="",
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
            total_points=total_points,
        )

    def _build_ui(self):
        row = 0

        self.first_name_title = ctk.CTkLabel(self.content, text="First Name", anchor="w")
        self.first_name_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.first_name_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.first_name_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.first_name_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.first_name_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.last_name_title = ctk.CTkLabel(self.content, text="Last Name", anchor="w")
        self.last_name_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.last_name_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.last_name_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.last_name_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.last_name_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.dob_title = ctk.CTkLabel(self.content, text="Date of Birth", anchor="w")
        self.dob_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.dob_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.dob_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.dob_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.dob_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.ncid_title = ctk.CTkLabel(self.content, text="NCID", anchor="w")
        self.ncid_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.ncid_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.ncid_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.ncid_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.ncid_value.grid(row=row, column=2, sticky="ew", pady=2)

        row += 1

        self.total_points_title = ctk.CTkLabel(self.content, text="Total Points", anchor="w")
        self.total_points_title.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        self.total_points_sep = ctk.CTkLabel(self.content, text=":", width=10, anchor="center")
        self.total_points_sep.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)

        self.total_points_value = ctk.CTkLabel(self.content, text="", anchor="w")
        self.total_points_value.grid(row=row, column=2, sticky="ew", pady=2)

    def set_player_info(self, first_name="", last_name="", date_of_birth="", ncid="", total_points=""):
        self.first_name_value.configure(text=first_name)
        self.last_name_value.configure(text=last_name)
        self.dob_value.configure(text=date_of_birth)
        self.ncid_value.configure(text=ncid)
        self.total_points_value.configure(text=total_points)

    def clear(self):
        self.set_player_info("", "", "", "", "")
