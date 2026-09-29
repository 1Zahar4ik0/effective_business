export interface paths {
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/official-announcements": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["official_announcements_api_official_announcements_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/config": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["config_api_config_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/demo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["demo_login_api_auth_demo_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/max": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["max_login_api_auth_max_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["me_api_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["logout_api_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["profile_api_profile_get"];
        put: operations["save_profile_api_profile_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/profile/questions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["profile_questions_api_profile_questions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["catalog_api_catalog_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/measures/{measure_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["measure_detail_api_measures__measure_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/matches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["matches_api_matches_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/preparation-plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["plans_api_preparation_plans_get"];
        put?: never;
        post: operations["create_plan_api_preparation_plans_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/preparation-plans/{plan_id}/items/{item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch: operations["check_item_api_preparation_plans__plan_id__items__item_id__patch"];
        trace?: never;
    };
    "/api/admin/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["admin_versions_api_admin_versions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["preview_rules_api_admin_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/measures": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["new_measure_api_admin_measures_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/versions/{version_id}/clone": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["clone_version_api_admin_versions__version_id__clone_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/versions/{version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put: operations["update_draft_api_admin_versions__version_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/admin/versions/{version_id}/{action}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["transition_api_admin_versions__version_id___action__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/max/webhook": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["webhook_api_max_webhook_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        AnnouncementSource: {
            url: string;
            document: string;
            sha256: string;
            finance_page: number;
            dates_page: number;
        };
        AnnouncementView: {
            measure_id: string;
            title: string;
            category: "grant" | "subsidy";
            audience: string;
            round: components["schemas"]["RoundInput"];
            funding_year: number;
            budget_rub: string;
            recipient_limit_rub?: string | null;
            limit_status: "stated" | "not_set_in_announcement";
            finance_note: string;
            legal_edition: string;
            source: components["schemas"]["AnnouncementSource"];
            checked_at: string;
            missing_evidence: string[];
            verification_scope: "announcement_facts_only";
            deadline_status: "not_started_in_notice" | "within_notice_dates" | "ended_in_notice";
            acceptance_status: "unconfirmed";
        };
        AnnouncementsView: {
            release_id: string;
            items: components["schemas"]["AnnouncementView"][];
        };
        "BusinessProfile-Input": {
            registration_region?: string | null;
            activity_region?: string | null;
            legal_form?: ("ip" | "company" | "cooperative" | "individual") | null;
            is_kfh?: boolean | null;
            tax_regime?: ("eshn" | "usn" | "npd" | "general") | null;
            sector?: ("crops" | "livestock" | "processing" | "mixed") | null;
            goal?: ("equipment" | "construction" | "working_capital" | "consultation") | null;
            expense_stage?: ("planned" | "incurred") | null;
            years_active?: number | null;
            own_funds?: number | string | null;
            is_sme?: boolean | null;
            special_category?: boolean | null;
            expense_year?: number | null;
            family_kfh_members?: number | null;
            requested_grant?: number | string | null;
        };
        "BusinessProfile-Output": {
            registration_region?: string | null;
            activity_region?: string | null;
            legal_form?: ("ip" | "company" | "cooperative" | "individual") | null;
            is_kfh?: boolean | null;
            tax_regime?: ("eshn" | "usn" | "npd" | "general") | null;
            sector?: ("crops" | "livestock" | "processing" | "mixed") | null;
            goal?: ("equipment" | "construction" | "working_capital" | "consultation") | null;
            expense_stage?: ("planned" | "incurred") | null;
            years_active?: number | null;
            own_funds?: string | null;
            is_sme?: boolean | null;
            special_category?: boolean | null;
            expense_year?: number | null;
            family_kfh_members?: number | null;
            requested_grant?: string | null;
        };
        CheckInput: {
            revision: number;
            done: boolean;
        };
        CheckView: {
            id: string;
            label: string;
            status: "PASS" | "FAIL" | "UNKNOWN";
            field: string | null;
            source_ref: string;
            children: components["schemas"]["CheckView"][];
        };
        DemoInput: {
            persona: "farmer" | "editor" | "second";
        };
        "Document-Input": {
            id: string;
            title: string;
            hint: string;
            condition?: components["schemas"]["Rule-Input"] | null;
        };
        "Document-Output": {
            id: string;
            title: string;
            hint: string;
            condition?: components["schemas"]["Rule-Output"] | null;
        };
        DocumentAssessment: {
            id: string;
            title: string;
            hint: string;
            condition?: components["schemas"]["Rule-Output"] | null;
            applicability: "required" | "not_applicable" | "unknown";
            check?: components["schemas"]["CheckView"] | null;
        };
        DraftInput: {
            revision: number;
            data: components["schemas"]["VersionData-Input"];
            rounds?: components["schemas"]["RoundInput"][];
        };
        HTTPValidationError: {
            detail?: components["schemas"]["ValidationError"][];
        };
        MatchView: {
            measure: components["schemas"]["MeasureView"];
            status: "PASS" | "FAIL" | "UNKNOWN";
            checks: components["schemas"]["CheckView"][];
            documents?: components["schemas"]["DocumentAssessment"][];
        };
        MatchesView: {
            evaluation_id: string;
            results: components["schemas"]["MatchView"][];
        };
        MaxInput: {
            init_data: string;
        };
        MeasureView: {
            id: string;
            title: string;
            category: string;
            synthetic: boolean;
            version_id: string;
            version: number;
            state: string;
            revision: number;
            data: components["schemas"]["VersionData-Output"];
            rounds: components["schemas"]["RoundView"][];
        };
        NewMeasure: {
            title: string;
            category: "grant" | "subsidy" | "consultation";
            synthetic: boolean;
            data: components["schemas"]["VersionData-Input"];
            rounds?: components["schemas"]["RoundInput"][];
        };
        PlanAssessment: {
            engine_version?: string | null;
            version_id?: string | null;
            version?: number | null;
            legal_edition?: string | null;
            round?: components["schemas"]["RoundView"] | null;
            assessed_at: string;
            profile: components["schemas"]["BusinessProfile-Output"];
            status: "PASS" | "FAIL" | "UNKNOWN";
            checks: components["schemas"]["CheckView"][];
            availability: string;
        };
        PlanDocument: {
            id: string;
            title: string;
            hint: string;
            condition?: components["schemas"]["Rule-Output"] | null;
            done: boolean;
            applicability?: ("required" | "not_applicable" | "unknown") | null;
            check?: components["schemas"]["CheckView"] | null;
        };
        PlanInput: {
            round_id: string;
        };
        PlanView: {
            id: string;
            revision: number;
            created_at: string;
            items: components["schemas"]["PlanDocument"][];
            measure: components["schemas"]["MeasureView"];
            round_id: string;
            needs_review: boolean;
            current_version_id: string | null;
            assessment?: components["schemas"]["PlanAssessment"] | null;
            profile_changed: boolean;
        };
        PreviewInput: {
            data: components["schemas"]["VersionData-Input"];
            profile: components["schemas"]["BusinessProfile-Input"];
        };
        PreviewView: {
            status: "PASS" | "FAIL" | "UNKNOWN";
            checks: components["schemas"]["CheckView"][];
        };
        ProfileQuestion: {
            field: "expense_year" | "family_kfh_members" | "requested_grant";
            label: string;
            hint: string;
            minimum: number;
            maximum: number;
            source_refs: string[];
            step: string;
        };
        RevisionInput: {
            revision: number;
        };
        RoundInput: {
            code: string;
            starts_at: string;
            ends_at: string;
            timezone: string;
            state: "announced" | "suspended" | "cancelled" | "unknown";
            acceptance_status: "unconfirmed" | "confirmed_open" | "closed";
            acceptance_checked_at?: string | null;
            application_url: string;
            channel: string;
        };
        RoundView: {
            code: string;
            starts_at: string;
            ends_at: string;
            timezone: string;
            state: "announced" | "suspended" | "cancelled" | "unknown";
            acceptance_status: "unconfirmed" | "confirmed_open" | "closed";
            acceptance_checked_at?: string | null;
            application_url: string;
            channel: string;
            id: string;
            availability: string;
        };
        "Rule-Input": {
            id: string;
            label: string;
            field?: string | null;
            op: "eq" | "in" | "gte" | "lte" | "all" | "any" | "manual";
            value?: string | number | boolean | string[] | null;
            children?: components["schemas"]["Rule-Input"][];
            source_ref: string;
        };
        "Rule-Output": {
            id: string;
            label: string;
            field?: string | null;
            op: "eq" | "in" | "gte" | "lte" | "all" | "any" | "manual";
            value?: string | number | boolean | string[] | null;
            children?: components["schemas"]["Rule-Output"][];
            source_ref: string;
        };
        SessionView: {
            user: components["schemas"]["UserView"];
            csrf: string;
        };
        Source: {
            title: string;
            url: string;
            reference: string;
            published_on: string;
        };
        UserView: {
            id: string;
            name: string;
            role: string;
            demo: boolean;
        };
        ValidationError: {
            loc: (string | number)[];
            msg: string;
            type: string;
            input?: unknown;
            ctx?: Record<string, never>;
        };
        "VersionData-Input": {
            publication_scope: "full" | "reference";
            reference_rule_ids?: string[];
            summary: string;
            benefit: string;
            operator: string;
            obligations: string;
            contact: string;
            rules?: components["schemas"]["Rule-Input"][];
            documents?: components["schemas"]["Document-Input"][];
            sources: components["schemas"]["Source"][];
            verified_at?: string | null;
            verification_status: "unverified" | "verified" | "conflict";
            valid_from?: string | null;
            valid_until?: string | null;
            validity_open_ended: boolean;
            validity_reference: string;
            legal_edition: string;
            research_checked_at?: string | null;
            missing_evidence?: string[];
            verification_notes: string;
        };
        "VersionData-Output": {
            publication_scope: "full" | "reference";
            reference_rule_ids?: string[];
            summary: string;
            benefit: string;
            operator: string;
            obligations: string;
            contact: string;
            rules?: components["schemas"]["Rule-Output"][];
            documents?: components["schemas"]["Document-Output"][];
            sources: components["schemas"]["Source"][];
            verified_at?: string | null;
            verification_status: "unverified" | "verified" | "conflict";
            valid_from?: string | null;
            valid_until?: string | null;
            validity_open_ended: boolean;
            validity_reference: string;
            legal_edition: string;
            research_checked_at?: string | null;
            missing_evidence?: string[];
            verification_notes: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    official_announcements_api_official_announcements_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnnouncementsView"];
                };
            };
        };
    };
    config_api_config_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    demo_login_api_auth_demo_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DemoInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    max_login_api_auth_max_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MaxInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    me_api_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    logout_api_auth_logout_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    profile_api_profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BusinessProfile-Output"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    save_profile_api_profile_put: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BusinessProfile-Input"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BusinessProfile-Output"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    profile_questions_api_profile_questions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProfileQuestion"][];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    catalog_api_catalog_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"][];
                };
            };
        };
    };
    measure_detail_api_measures__measure_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                measure_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"];
                };
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    matches_api_matches_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MatchesView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    plans_api_preparation_plans_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlanView"][];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    create_plan_api_preparation_plans_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlanInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlanView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    check_item_api_preparation_plans__plan_id__items__item_id__patch: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path: {
                plan_id: string;
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CheckInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlanView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    admin_versions_api_admin_versions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"][];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    preview_rules_api_admin_preview_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PreviewInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PreviewView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    new_measure_api_admin_measures_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NewMeasure"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    clone_version_api_admin_versions__version_id__clone_post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_draft_api_admin_versions__version_id__put: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DraftInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    transition_api_admin_versions__version_id___action__post: {
        parameters: {
            query?: never;
            header: {
                "X-App-Request": "1";
            };
            path: {
                version_id: string;
                action: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RevisionInput"];
            };
        };
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeasureView"];
                };
            };
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    webhook_api_max_webhook_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
}
