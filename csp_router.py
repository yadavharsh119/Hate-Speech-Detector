from constraint import Problem, FunctionConstraint

def assign_moderator(tweet_id, tweet_language, tweet_severity, moderators_list):
    """
    Solves the Constraint Satisfaction Problem for an incoming flagged tweet.

    Hard Constraints:
      1. Language Match: Tweet language in moderator's language list.
      2. Workload Capacity: Moderator active_load < max_capacity.

    Priority Constraint:
      3. Seniority: If tweet_severity == 'Severe', force role == 'Senior'.

    Optimization (Tie-Breaking):
      Picks the candidate with the lowest workload ratio (active_load / max_capacity).
    """
    problem = Problem()

    # 1. Define Variable (The single tweet being routed)
    problem.addVariable("tweet", moderators_list)

    # 2. Hard Constraint 1: Capacity Check
    def capacity_check(mod):
        return mod["active_load"] < mod["max_capacity"]

    # 3. Hard Constraint 2: Language Check
    def language_check(mod):
        return tweet_language in mod["languages"]

    # 4. Priority Constraint 3: Seniority Check for Severe Tweets
    def seniority_check(mod):
        if tweet_severity == "Severe":
            return mod["role"] == "Senior"
        return True

    # Apply constraints to solver
    problem.addConstraint(FunctionConstraint(capacity_check), ["tweet"])
    problem.addConstraint(FunctionConstraint(language_check), ["tweet"])
    problem.addConstraint(FunctionConstraint(seniority_check), ["tweet"])

    # Execute Solver
    solutions = problem.getSolutions()

    # Fallback: No available moderator satisfies constraints
    if not solutions:
        return {
            "status": "QUEUED",
            "tweet_id": tweet_id,
            "assigned_moderator": None,
            "decision_reason": f"No available moderator found for language '{tweet_language}' with severity '{tweet_severity}' and active capacity."
        }

    # Extract candidate moderators
    valid_candidates = [sol["tweet"] for sol in solutions]

    # Optimization Tie-Breaker: Select candidate with lowest workload ratio
    selected_mod = min(valid_candidates, key=lambda m: m["active_load"] / m["max_capacity"])

    # Calculate utilization percentage for audit log
    utilization_pct = round((selected_mod["active_load"] / selected_mod["max_capacity"]) * 100, 1)

    # Return structured Decision Explanation Log
    return {
        "status": "ASSIGNED",
        "tweet_id": tweet_id,
        "assigned_moderator": selected_mod["id"],
        "moderator_name": selected_mod["name"],
        "decision_reason": (
            f"Matched language '{tweet_language}'; "
            f"{'Enforced Senior role due to Severe rating; ' if tweet_severity == 'Severe' else ''}"
            f"Selected {selected_mod['name']} with lowest workload ratio ({utilization_pct}% capacity used)."
        )
    }


class PriorityBufferQueue:
    """
    Manages unassigned tweets when all matching moderators are at full capacity.
    Orders tasks by Severity (Severe -> Moderate -> Mild) and arrival time.
    """
    SEVERITY_ORDER = {"Severe": 1, "Moderate": 2, "Mild": 3}

    def __init__(self):
        self.queue = []

    def push(self, tweet_data):
        self.queue.append(tweet_data)
        # Sort queue: Severe first, then Moderate, then Mild
        self.queue.sort(key=lambda t: self.SEVERITY_ORDER.get(t.get("severity"), 4))

    def pop(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def get_queue_length(self):
        return len(self.queue)