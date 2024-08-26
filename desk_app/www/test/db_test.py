# import orm
# import asyncio
# from model import User


# async def main():
#     loop = asyncio.get_running_loop()
#     await orm.create_pool(loop, user="roamer", password="roamer", database="awesome")

#     # u = User(
#     #     name="Test2",
#     #     email="test2@example.com",
#     #     passwd="1234567890",
#     #     image="about:blank",
#     # )

#     # u1 = await User.findAll(
#     #     where="`name`=?",
#     #     args=[
#     #         "Test2",
#     #     ],
#     # )

#     u2 = await User.findAll()
#     print(u2)
#     u2[0].name = "Test"
#     await u2[0].update()

#     await orm.close_pool()


# if __name__ == "__main__":
#     asyncio.run(main())
