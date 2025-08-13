# Artifacts Tool Improvement Plan

This document outlines the required improvements and bug fixes for the `artifacts` tool, based on a comprehensive test suite. This is intended as a work order for a coding agent.

---

## 1. Critical Bug: `list` Operation Filtering is Non-Functional

-   **The Issue:** The `list` operation does not filter results by tags.
-   **Observed Behavior:** When calling `list` with the `tags` parameter (e.g., `{"operation": "list", "tags": ["my_tag"]}`), the tool returns all artifacts in the database, ignoring the provided filter.
-   **Expected Behavior:** The `list` operation should return only the artifacts that contain the tag(s) specified in the `tags` parameter.
-   **Suggested Action:** Implement the filtering logic in the `list` operation's backend code. The query to the database must be modified to include a `WHERE` clause that checks for the presence of the provided tags.

---

## 2. API Ergonomics: `update` Operation Requires Full Payload

-   **The Issue:** The `update` operation requires the `data` payload to be sent even when the user only intends to modify the tags.
-   **Observed Behavior:** A call to `update` with only `artifact_id` and `tags` fails with an error stating that `data` is required.
-   **Expected Behavior:** The `update` operation should allow for partial updates. If only `tags` are provided, it should update the tags without requiring the `data` payload. If only `data` is provided, it should update the content. If both are provided, it should update both.
-   **Suggested Action:** Refactor the `update` endpoint to handle partial updates. Check for the presence of `data` and `tags` parameters independently and build the update query accordingly. This will make the API more flexible and intuitive.

---

## 3. Design Clarification: Idempotent `create` Behavior

-   **The Issue:** The `create` operation's idempotent nature has a potentially confusing side effect: it silently discards new tags when a content hash match is found.
-   **Observed Behavior:** Calling `create` with existing content but new tags returns the ID of the existing artifact and does not add the new tags to it.
-   **Expected Behavior:** While the content-based idempotency is a powerful feature, the behavior should be more transparent and flexible.
-   **Suggested Action:**
    1.  **(High Priority)** Update the tool's documentation and help text to clearly state that `create` is a 'get-or-create' operation based on content hash and that tags are ignored on a hash match.
    2.  **(Optional Enhancement)** Consider adding a parameter like `merge_tags: true` to the `create` operation. If this flag is present and a hash match occurs, the tool would add the new tags to the existing artifact instead of discarding them.

---

## 4. Documentation: Inconsistent/Undocumented Parameter Names

-   **The Issue:** The correct parameter names for core operations (`data` for create, `artifact_id` for read/update/delete) were not immediately obvious from the tool's description and had to be discovered via trial and error.
-   **Observed Behavior:** Calls failed with parameter-related errors (e.g., using `content` instead of `data`, or `id` instead of `artifact_id`).
-   **Expected Behavior:** The tool's documentation (e.g., help text, schema definition) should explicitly list all required and optional parameters for each operation.
-   **Suggested Action:** Review and update the tool's description and any associated documentation to accurately reflect the required parameters for all its operations (`create`, `read`, `update`, `delete`, `list`, `stats`).