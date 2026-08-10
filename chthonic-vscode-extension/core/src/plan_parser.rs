use crate::edit_plan::EditPlan;

pub fn parse_plan_from_text(text: &str) -> Option<EditPlan> {
    for candidate in json_candidates(text) {
        if let Ok(plan) = serde_json::from_str::<EditPlan>(&candidate) {
            if !plan.plan_id.trim().is_empty() && !plan.edits.is_empty() {
                return Some(plan);
            }
        }
    }
    None
}

fn json_candidates(text: &str) -> Vec<String> {
    let mut candidates = fenced_json_candidates(text);
    candidates.extend(balanced_json_candidates(text));
    candidates
}

fn fenced_json_candidates(text: &str) -> Vec<String> {
    let mut candidates = Vec::new();
    let mut rest = text;

    while let Some(start) = rest.find("```") {
        rest = &rest[start + 3..];
        let content_start = rest
            .strip_prefix("json")
            .or_else(|| rest.strip_prefix("JSON"))
            .unwrap_or(rest);
        let content_start = content_start
            .strip_prefix("\r\n")
            .or_else(|| content_start.strip_prefix('\n'))
            .unwrap_or(content_start);

        let Some(end) = content_start.find("```") else {
            break;
        };
        candidates.push(content_start[..end].trim().to_owned());
        rest = &content_start[end + 3..];
    }

    candidates
}

fn balanced_json_candidates(text: &str) -> Vec<String> {
    let mut candidates = Vec::new();
    let mut starts = text.match_indices('{').map(|(index, _)| index).peekable();

    while let Some(start) = starts.next() {
        let mut depth = 0usize;
        let mut in_string = false;
        let mut escaped = false;

        for (relative_index, ch) in text[start..].char_indices() {
            if escaped {
                escaped = false;
                continue;
            }
            if ch == '\\' && in_string {
                escaped = true;
                continue;
            }
            if ch == '"' {
                in_string = !in_string;
                continue;
            }
            if in_string {
                continue;
            }

            match ch {
                '{' => depth += 1,
                '}' => {
                    depth = depth.saturating_sub(1);
                    if depth == 0 {
                        let end = start + relative_index + ch.len_utf8();
                        candidates.push(text[start..end].to_owned());
                        break;
                    }
                }
                _ => {}
            }
        }
    }

    candidates
}

#[cfg(test)]
mod tests {
    use super::*;

    const PLAN_JSON: &str = r#"{
        "planId": "plan-live-1",
        "summary": "insert comment",
        "edits": [
            {
                "uri": "file:///C:/tmp/probe.txt",
                "range": {
                    "start": { "line": 0, "character": 0 },
                    "end": { "line": 0, "character": 0 }
                },
                "newText": "// hello\n"
            }
        ],
        "requiredPermissions": ["writeFile"],
        "createdAtMs": 42
    }"#;

    #[test]
    fn parses_raw_edit_plan() {
        let plan = parse_plan_from_text(PLAN_JSON).unwrap();
        assert_eq!(plan.plan_id, "plan-live-1");
        assert_eq!(plan.edits.len(), 1);
    }

    #[test]
    fn parses_fenced_edit_plan() {
        let text = format!("Here is the plan:\n```json\n{PLAN_JSON}\n```\nReview it.");
        let plan = parse_plan_from_text(&text).unwrap();
        assert_eq!(plan.required_permissions.len(), 1);
    }

    #[test]
    fn rejects_missing_plan() {
        assert!(parse_plan_from_text("no plan here").is_none());
    }

    #[test]
    fn rejects_invalid_shape() {
        assert!(parse_plan_from_text(r#"{"planId":"plan-1","edits":[]}"#).is_none());
    }
}
