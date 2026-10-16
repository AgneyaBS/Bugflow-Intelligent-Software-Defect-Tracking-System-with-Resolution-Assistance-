
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/chatbot",
    tags=["AI Chatbot"],
)


class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation: list[ChatMessage] = Field(
        default_factory=list,
        max_length=12,
    )


class ChatResponse(BaseModel):
    reply: str


def generate_reply(message: str) -> str:
    """Provide BugFlow guidance using local Python rules."""

    text = re.sub(r"\s+", " ", message.strip().lower())

    if not text:
        return "Please enter a question so I can help."
    
    # THANK YOU AND POLITE RESPONSES
    if re.search(
        r"\b(thank you|thanks|thank you so much|thx)\b",
        text
    ):
        return (
            "You're welcome! 😊 I'm here to help you with BugFlow. "
            "You can ask me about reporting issues, checking issue status, "
            "assignments, priorities, resolution assistance, or troubleshooting."
        )

    if re.search(
        r"\b(you are welcome|you're welcome|welcome)\b",
        text
    ):
        return (
            "Thank you! 😊 Feel free to ask me anything about BugFlow. "
            "I can help with issue reporting, status tracking, assignments, "
            "priorities, resolution assistance, and troubleshooting."
        )


    # -----------------------------------------------------
    # 1. ISSUE STATUS
    # -----------------------------------------------------

    if (
        re.search(
            r"\b(status|progress|track|tracking|state)\b",
            text,
        )
        and re.search(
            r"\b(issue|issues|bug|bugs|defect|defects|ticket|tickets)\b",
            text,
        )
    ) or re.search(
        r"\b(my issues|status of my issue|status of my bug|"
        r"where is my issue|what happened to my issue)\b",
        text,
    ):
        return (
            "To check your issue status in BugFlow:\n\n"
            "1. Open My Issues from the user sidebar.\n"
            "2. Find the issue you reported.\n"
            "3. Review its current status, such as Open, In Progress, "
            "or Resolved, if displayed.\n"
            "4. Open the issue details to review any available comments "
            "or updates.\n"
            "5. If the issue has not been updated, contact the administrator "
            "or assigned developer through the available project workflow.\n\n"
            "This is general guidance. I have not retrieved your actual "
            "issue records or live status from the database."
        )

    # -----------------------------------------------------
    # 2. ASSIGN ISSUES TO DEVELOPERS
    # -----------------------------------------------------

    if re.search(
        r"\b(assign|assignment|assignee|allocate|developer)\b",
        text,
    ) and re.search(
        r"\b(issue|bug|defect|developer|assign|assignee)\b",
        text,
    ):
        return (
            "To assign an issue to a developer in BugFlow:\n\n"
            "1. Open the Admin Dashboard.\n"
            "2. Navigate to All Issues.\n"
            "3. Select the issue you want to assign.\n"
            "4. Look for the Assignee, Assigned To, or Developer field.\n"
            "5. Select an appropriate developer, if the option is available.\n"
            "6. Save or update the issue.\n"
            "7. Reopen the issue details to verify the assignment.\n\n"
            "If you are logged in as a regular user, you may need an "
            "administrator to assign the issue.\n\n"
            "These are guidance steps. The chatbot does not assign issues."
        )

    # -----------------------------------------------------
    # 3. REVIEW NEW ISSUES
    # -----------------------------------------------------

    if re.search(
        r"\b(review|reviewing|newly reported|newly created|"
        r"new issues|incoming|submitted issues)\b",
        text,
    ) and re.search(
        r"\b(issue|issues|bug|bugs|defect|defects|reported|submitted)\b",
        text,
    ):
        return (
            "To review a newly reported issue in BugFlow:\n\n"
            "1. Open the appropriate issue list.\n"
            "2. Find the newly reported issue.\n"
            "3. Read its title, description, and reproduction steps.\n"
            "4. Check the expected and actual behaviour.\n"
            "5. Review its category, severity, and priority.\n"
            "6. Check any available attachments and comments.\n"
            "7. Request clarification if important information is missing.\n"
            "8. Follow the available workflow to assign or update the issue.\n\n"
            "Administrators generally handle assignment and issue review."
        )
        
    # -----------------------------------------------------
    # ISSUE PRIORITY EXPLANATION
    # -----------------------------------------------------

    if re.search(
        r"\b(priority|priorities|severity|urgent|critical)\b",
        text,
    ) and re.search(
        r"\b(mean|means|meaning|explain|understand|levels|"
        r"difference|what|how|issue|issues|bug|bugs)\b",
        text,
    ):
        return (
            "BugFlow uses issue priority to indicate how quickly an issue "
            "should be investigated and addressed.\n\n"
            "Priority levels:\n\n"
            "1. URGENT: Requires immediate attention because of its "
            "serious impact.\n\n"
            "2. HIGH: Needs prompt investigation and resolution.\n\n"
            "3. MEDIUM: Should be addressed as part of normal work "
            "planning.\n\n"
            "4. LOW: Can generally be handled when higher-priority "
            "issues have been addressed.\n\n"
            "How BugFlow calculates priority:\n\n"
            "Priority Score = Severity Weight x Category Urgency Weight\n\n"
            "Severity weights:\n"
            "- CRITICAL = 4\n"
            "- MAJOR = 3\n"
            "- MINOR = 2\n"
            "- TRIVIAL = 1\n\n"
            "Category urgency weights:\n"
            "- HIGH = 3\n"
            "- MEDIUM = 2\n"
            "- LOW = 1\n\n"
            "Priority score mapping:\n"
            "- Score 10 or higher: URGENT\n"
            "- Score 7 to 9: HIGH\n"
            "- Score 4 to 6: MEDIUM\n"
            "- Score below 4: LOW\n\n"
            "Example: MAJOR severity (3) multiplied by HIGH category "
            "urgency (3) gives a score of 9, which results in HIGH priority.\n\n"
            "Priority indicates how quickly an issue should be addressed; "
            "severity describes how seriously the issue affects the system."
        )


    # -----------------------------------------------------
    # 4. CRITICAL AND URGENT ISSUES
    # -----------------------------------------------------

    if re.search(
        r"\b(critical|urgent|emergency|high priority|"
        r"severity|priority)\b",
        text,
    ):
        return (
            "When handling a critical or urgent BugFlow issue:\n\n"
            "1. Open the issue and confirm its severity and priority.\n"
            "2. Assess the impact on users and important operations.\n"
            "3. Review reproduction steps, logs, and available evidence.\n"
            "4. Notify the administrator or responsible developer.\n"
            "5. Track investigation progress and record relevant updates.\n"
            "6. Test the proposed fix before confirming resolution.\n\n"
            "BugFlow's configured priority calculator combines severity "
            "and category urgency. Check the actual calculated priority "
            "instead of assuming every critical issue has the same score."
        )

    # -----------------------------------------------------
    # 5. RESOLUTION ASSISTANCE
    # -----------------------------------------------------

    if re.search(
        r"\b(resolution assistance|resolution suggestion|"
        r"suggested solution|recommended fix|view resolution|"
        r"solution for an issue|fix an issue)\b",
        text,
    ):
        return (
            "To view resolution assistance in BugFlow:\n\n"
            "1. Open My Issues or the relevant issue list.\n"
            "2. Select the issue you want to investigate.\n"
            "3. Open its details.\n"
            "4. Find the Resolution Assistance section, if available.\n"
            "5. Review the suggested troubleshooting steps.\n"
            "6. Compare the suggestions with the issue description and logs.\n"
            "7. Test any proposed fix and document the result.\n\n"
            "A suggested solution is not proof that the issue is fixed. "
            "Verify the result before marking an issue as resolved."
        )

    # -----------------------------------------------------
    # 6. REPORT OR CREATE AN ISSUE
    # -----------------------------------------------------

    if re.search(
        r"\b(report|create|submit|raise)\b",
        text,
    ) and re.search(
        r"\b(bug|issue|defect|problem)\b",
        text,
    ):
        return (
            "To report an issue in BugFlow:\n\n"
            "1. Open Report Issue from the user sidebar.\n"
            "2. Enter a clear and descriptive title.\n"
            "3. Explain the expected and actual behaviour.\n"
            "4. Select the appropriate category and severity.\n"
            "5. Include reproduction steps and relevant evidence.\n"
            "6. Submit the issue.\n"
            "7. Open My Issues to find your reported issue and check "
            "its status.\n\n"
            "Clear reproduction steps help developers investigate faster."
        )

    # -----------------------------------------------------
    # 7. USER MANAGEMENT
    # -----------------------------------------------------

    if re.search(
        r"\b(user management|manage users|user accounts|"
        r"manage user|user roles|roles and permissions|"
        r"activate user|deactivate user)\b",
        text,
    ):
        return (
            "User management is generally an administrator task.\n\n"
            "An administrator can open the Admin Dashboard, navigate "
            "to Users, find an account, and use the available controls "
            "to manage its role or account status.\n\n"
            "Regular users should contact an administrator if they "
            "need changes to their account permissions."
        )

    # -----------------------------------------------------
    # 8. BACKEND AND API ERRORS
    # -----------------------------------------------------

    if re.search(
        r"\b(troubleshoot|debug|fix|investigate|diagnose|"
        r"resolve|error|errors|problem|problems|not working)\b",
        text,
    ) and re.search(
        r"\b(backend|server|api|endpoint|500|502|503|504|404)\b",
        text,
    ):
        return (
            "To troubleshoot a BugFlow backend or API error:\n\n"
            "1. Confirm that the FastAPI backend is running.\n"
            "2. Open http://127.0.0.1:8000/docs to inspect available routes.\n"
            "3. Check the browser Network tab for the failed request.\n"
            "4. Record the HTTP status code and response detail.\n"
            "5. Inspect the backend terminal for the corresponding error.\n"
            "6. Check authentication, request fields, and database connectivity.\n"
            "7. Reproduce the problem and test a targeted fix.\n\n"
            "HTTP 401 usually indicates an authentication issue, 403 "
            "indicates insufficient permission, 404 indicates a missing "
            "route or resource, and 500 indicates a server error.\n\n"
            "Never share passwords, access tokens, or database secrets."
        )

    # -----------------------------------------------------
    # 9. DATABASE PROBLEMS
    # -----------------------------------------------------

    if re.search(
        r"\b(database|postgres|postgresql|sql|query|db connection)\b",
        text,
    ):
        return (
            "To troubleshoot a BugFlow database problem:\n\n"
            "1. Confirm that PostgreSQL is running.\n"
            "2. Check the database host, port, and database name.\n"
            "3. Verify the environment configuration locally.\n"
            "4. Inspect backend logs for SQLAlchemy or psycopg2 errors.\n"
            "5. Verify that the required tables exist.\n"
            "6. Check the failing query and transaction details.\n\n"
            "Never share database passwords or connection strings."
        )

    # -----------------------------------------------------
    # 10. LOGIN AND AUTHENTICATION
    # -----------------------------------------------------

    if re.search(
        r"\b(login|log in|signin|sign in|jwt|token|"
        r"authentication|unauthorized|401|403)\b",
        text,
    ):
        return (
            "For a BugFlow login or authentication problem:\n\n"
            "1. Verify your login credentials.\n"
            "2. Check whether your account is active.\n"
            "3. Sign in again if your session has expired.\n"
            "4. Confirm that the frontend sends the bearer token.\n"
            "5. For HTTP 403, check the endpoint's permission settings.\n"
            "6. Inspect the backend logs for additional details.\n\n"
            "Never share a real JWT, password, or secret."
        )

    # -----------------------------------------------------
    # 11. FRONTEND PROBLEMS
    # -----------------------------------------------------

    if re.search(
        r"\b(frontend|ui|css|html|javascript|button|"
        r"layout|sidebar|style|page)\b",
        text,
    ):
        return (
            "To troubleshoot a BugFlow frontend problem:\n\n"
            "1. Open your browser's Developer Tools.\n"
            "2. Check the Console for JavaScript errors.\n"
            "3. Check the Network tab for failed requests.\n"
            "4. Verify stylesheet and script paths.\n"
            "5. Check that HTML element IDs match the JavaScript.\n"
            "6. Ensure scripts and event handlers are not duplicated.\n"
            "7. Refresh the page and reproduce the problem.\n\n"
            "Share the relevant code or error message for more specific help."
        )

    # -----------------------------------------------------
    # 12. TESTING
    # -----------------------------------------------------

    if re.search(
        r"\b(test|testing|pytest|test case|reproduce|regression)\b",
        text,
    ):
        return (
            "A useful BugFlow testing workflow is:\n\n"
            "1. Record the preconditions.\n"
            "2. Write clear reproduction steps.\n"
            "3. Define the expected result.\n"
            "4. Record the actual result.\n"
            "5. Test normal, boundary, and invalid inputs.\n"
            "6. Retest after the fix and check for regressions.\n\n"
            "For backend tests, run 'python -m pytest' from the "
            "appropriate project directory."
        )

    # -----------------------------------------------------
    # 13. GENERAL RESOLUTION AND DEBUGGING
    # -----------------------------------------------------

    if re.search(
        r"\b(resolve|resolution|fix|debug|troubleshoot|solving)\b",
        text,
    ):
        return (
            "To investigate a software issue:\n\n"
            "1. Reproduce the problem consistently.\n"
            "2. Read the error message and relevant logs.\n"
            "3. Identify the component where the failure occurs.\n"
            "4. Check recent code and configuration changes.\n"
            "5. Make one targeted change and run the relevant tests.\n"
            "6. Verify the fix and document the resolution.\n\n"
            "Share the expected behaviour, actual behaviour, and "
            "error message for more targeted troubleshooting."
        )

    # -----------------------------------------------------
    # 14. GREETINGS
    # -----------------------------------------------------

    if re.fullmatch(
        r"(hi|hello|hey|good morning|good afternoon|good evening)[!. ]*",
        text,
    ):
        return (
            "Hello! Welcome to BugFlow Support.\n\n"
            "I can guide you through reporting issues, checking issue "
            "status, understanding priorities, viewing resolution "
            "assistance, and troubleshooting common problems.\n\n"
            "Type your question in your own words to get started."
        )

    # -----------------------------------------------------
    # 15. HELP
    # -----------------------------------------------------

    if re.search(
        r"\b(help|what can you do|how can you help|available features)\b",
        text,
    ):
        return (
            "I can help you with common BugFlow tasks:\n\n"
            "• Reporting a bug or issue\n"
            "• Checking issue status and progress\n"
            "• Understanding severity and priority\n"
            "• Finding resolution assistance\n"
            "• Understanding issue assignment\n"
            "• Troubleshooting frontend, backend, and database problems\n"
            "• Planning tests and verifying fixes\n\n"
            "Ask a question in your own words to get relevant guidance."
        )

    # -----------------------------------------------------
    # 16. PROJECT AND WORKFLOW
    # -----------------------------------------------------

    if re.search(
        r"\b(project|bugflow|issue tracking|workflow)\b",
        text,
    ):
        return (
            "BugFlow is an issue-tracking and resolution platform.\n\n"
            "It helps teams report software defects, review their "
            "severity and priority, coordinate assignments, monitor "
            "progress, and access resolution guidance.\n\n"
            "I provide guidance using local Python rules. I do not "
            "automatically inspect or change live project records."
        )

    # -----------------------------------------------------
    # 17. DEFAULT RESPONSE
    # -----------------------------------------------------

    return (
        "I don't have a specific built-in answer for that question yet.\n\n"
        "You can ask about reporting issues, checking issue status, "
        "assignments, priority, resolution assistance, testing, or "
        "troubleshooting.\n\n"
        "Try describing your question in a little more detail."
    )


# ---------------------------------------------------------
# CHATBOT ENDPOINT
# Both authenticated regular users and admins are allowed.
# ---------------------------------------------------------

@router.post("/message", response_model=ChatResponse)
def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    # Keep the authentication check supplied by get_current_user.
    # Reject inactive accounts.
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive.",
        )

    # Intentionally no ADMIN-only role check here.
    # Any authenticated active user can access the chatbot.
    reply = generate_reply(request.message)

    return ChatResponse(reply=reply)
