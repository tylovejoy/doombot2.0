import discord

from views.basic import ConfirmButton


class RecordSubmitView(discord.ui.View):
    def __init__(self, *, timeout=None, confirm_disabled=False):
        super().__init__(timeout=timeout)

        self.confirm = ConfirmButton(row=1, disabled=confirm_disabled)
        self.add_item(self.confirm)
