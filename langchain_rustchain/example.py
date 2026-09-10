from rustchain_tool import RustChainTool


def main() -> None:
    tool = RustChainTool()
    print("health:", tool.invoke({"action": "get_node_health"}))
    # Public read-only demonstration; replace with any RTC wallet when desired.
    print("bounties:", tool.invoke({"action": "list_bounties", "limit": 3}))
    print("epoch:", tool.invoke({"action": "get_current_epoch"}))


if __name__ == "__main__":
    main()
