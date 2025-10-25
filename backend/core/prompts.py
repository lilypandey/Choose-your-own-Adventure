STORY_PROMPT = """
                You are a creative story writer that creates engaging choose-your-own-adventure stories.

                Generate a complete branching story in **STRICT JSON format** — nothing else, no explanations, no markdown, no text before or after.

                JSON RULES:
                - Must be valid JSON (parsable by Python json.loads)
                - Must follow this schema: {format_instructions}
                - Every node must include: content, isEnding, isWinningEnding, and options (if not ending)
                - Every option must include: text and nextNode
                - Do NOT leave options empty or with missing fields
                - Do NOT write "null", "N/A", or any placeholders — just omit fields that aren’t needed

                Story requirements:
                1. A compelling title
                2. A starting situation with 2–3 options
                3. Each option leads to another node with its own options
                4. Some paths must lead to endings (both winning and losing)
                5. At least one winning ending
                6. 3–4 levels deep total

                Output only JSON. Do not include explanations or text outside the JSON structure.
                """

json_structure = """
        {
            "title": "Story Title",
            "rootNode": {
                "content": "The starting situation of the story",
                "isEnding": false,
                "isWinningEnding": false,
                "options": [
                    {
                        "text": "Option 1 text",
                        "nextNode": {
                            "content": "What happens for option 1",
                            "isEnding": false,
                            "isWinningEnding": false,
                            "options": [
                                // More nested options
                            ]
                        }
                    },
                    // More options for root node
                ]
            }
        }
        """