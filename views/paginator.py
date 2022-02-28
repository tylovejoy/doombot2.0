from copy import deepcopy
from typing import List, Union

import discord


class Paginator(discord.ui.View):
    """ "A view for paginating multiple embeds."""

    def __init__(
        self,
        embeds: List[Union[discord.Embed, str]],
        author: discord.Member,
        timeout=None,
    ):
        """Init paginator."""
        super().__init__(timeout=timeout)
        self.pages = embeds
        self.author = author
        self._curr_page = 0
        if len(self.pages) == 1:
            self.first.disabled = True
            self.back.disabled = True
            self.next.disabled = True
            self.last.disabled = True

    async def start(self, interaction: discord.Interaction):
        if isinstance(self.pages[0], str):
            await interaction.edit_original_message(
                content=self.formatted_pages[0],
                view=self,
            )
        else:

            await interaction.edit_original_message(
                embed=self.formatted_pages[0],
                view=self,
            )
        await self.wait()

    @property
    def formatted_pages(self) -> List[Union[discord.Embed, str, None]]:
        """The embeds with formatted footers to act as pages."""
        if not self.pages:
            return None

        if isinstance(self.pages[0], str):
            return self.pages

        pages = deepcopy(self.pages)  # copy by value not reference
        for page in pages:
            if page.footer.text == discord.Embed.Empty:
                page.set_footer(text=f"({pages.index(page) + 1}/{len(pages)})")
            else:
                page_index = pages.index(page)
                if page.footer.icon_url == discord.Embed.Empty:
                    page.set_footer(
                        text=f"{page.footer.text} - ({page_index + 1}/{len(pages)})"
                    )
                else:
                    page.set_footer(
                        icon_url=page.footer.icon_url,
                        text=f"{page.footer.text} - ({page_index + 1}/{len(pages)})",
                    )
        return pages

    async def interaction_check(self, item, interaction: discord.Interaction) -> bool:
        """Check if the interaction user is the original users who started the interaction."""
        if interaction.user == self.author:
            return True
        return False

    async def on_timeout(self) -> None:
        """Stop view on timeout."""
        self.stop()
        return await super().on_timeout()

    @discord.ui.button(label="First", emoji="⏮")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button component to return to the first pagination page."""
        if len(self.pages) == 1:
            button.disabled = True
        self._curr_page = 0
        return await self.change_page(interaction)

    @discord.ui.button(label="Back", emoji="◀")
    async def back(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button component to go back to the last pagination page."""
        if len(self.pages) == 1:
            button.disabled = True
        if self._curr_page == 0:
            self._curr_page = len(self.pages) - 1
        else:
            self._curr_page -= 1

        return await self.change_page(interaction)

    async def change_page(self, interaction):
        if isinstance(self.pages[0], str):
            await interaction.response.edit_message(
                content=self.formatted_pages[self._curr_page], view=self
            )
            return
        await interaction.response.edit_message(
            embed=self.formatted_pages[self._curr_page], view=self
        )

    @discord.ui.button(label="Next", emoji="▶")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button component to go to the next pagination page."""
        if len(self.pages) == 1:
            button.disabled = True
        if self._curr_page == len(self.pages) - 1:
            self._curr_page = 0
        else:
            self._curr_page += 1

        return await self.change_page(interaction)

    @discord.ui.button(label="Last", emoji="⏭")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button component to go to the last pagination page."""
        if len(self.pages) == 1:
            button.disabled = True
        self._curr_page = len(self.pages) - 1

        return await self.change_page(interaction)
