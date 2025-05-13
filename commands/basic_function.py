from discord.ext import commands

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='안녕', aliases=['hi'])
    async def hello(self, ctx):
        """인사합니다."""
        await ctx.send('안녕하세요!')

    @commands.command(name='도움')
    async def help_command(self, ctx):
        """도움말을 보여줍니다."""
        help_message = (
            ".도움/help - 도움말을 보여줍니다.\n"
            ".안녕/hi - 인사합니다.\n"
            ".승률 [닉네임#태그] [서버(기본값 kr)] - 시즌 솔로랭크 승률을 보여줍니다.\n"
        )
        await ctx.send(help_message)