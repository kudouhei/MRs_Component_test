import React from "react";
import {render, screen} from "@testing-library/react";

import {FieldErrorRoot} from "./source";

describe("Heroui FieldErrorRoot (data_test fixture)", () => {
  it("renders a validation message for assistive tech", () => {
    const {container} = render(
      <FieldErrorRoot id="name-err">Name is required before you can continue.</FieldErrorRoot>,
    );
    expect(screen.getByText(/name is required/i)).toBeTruthy();
    expect(container.textContent).toMatch(/before you can continue/i);
  });

  it("supports render-prop style children", () => {
    render(
      <FieldErrorRoot>
        {() => <span>Custom error presentation</span>}
      </FieldErrorRoot>,
    );
    expect(screen.getByText(/custom error presentation/i)).toBeTruthy();
  });

  it("shows email format validation copy", () => {
    render(
      <FieldErrorRoot id="email-format-err">
        Please enter a valid email address such as name@company.com.
      </FieldErrorRoot>,
    );
    expect(screen.getByText(/valid email address/i)).toBeTruthy();
    expect(screen.getByText(/@company\.com/)).toBeTruthy();
  });

  it("shows min and max length constraints", () => {
    render(
      <FieldErrorRoot>
        Password must be between 12 and 128 characters and include uppercase, lowercase, and a digit.
      </FieldErrorRoot>,
    );
    expect(screen.getByText(/between 12 and 128/i)).toBeTruthy();
    expect(screen.getByText(/uppercase/i)).toBeTruthy();
  });

  it("shows pattern mismatch for alphanumeric codes", () => {
    render(
      <FieldErrorRoot id="sku-err">SKU must match pattern AAAA-0000 (letters then hyphen then digits).</FieldErrorRoot>,
    );
    expect(screen.getByText(/AAAA-0000/)).toBeTruthy();
    expect(screen.getByText(/pattern/i)).toBeTruthy();
  });

  it("shows server-side conflict errors", () => {
    render(
      <FieldErrorRoot>
        That username is already taken. Pick another handle or sign in instead.
      </FieldErrorRoot>,
    );
    expect(screen.getByText(/already taken/i)).toBeTruthy();
    expect(screen.getByText(/sign in instead/i)).toBeTruthy();
  });

  it("shows numeric range errors for quantity fields", () => {
    render(
      <FieldErrorRoot>Quantity must be between 1 and 99 inclusive for this shipment.</FieldErrorRoot>,
    );
    expect(screen.getByText(/between 1 and 99/i)).toBeTruthy();
    expect(screen.getByText(/shipment/i)).toBeTruthy();
  });

  it("applies className for emphasis styling on critical errors", () => {
    const {container} = render(
      <FieldErrorRoot className="text-destructive font-medium" id="critical-card">
        Payment was declined — update your card or use a different funding source.
      </FieldErrorRoot>,
    );
    expect(container.querySelector("#critical-card")?.className).toContain("text-destructive");
    expect(screen.getByText(/payment was declined/i)).toBeTruthy();
  });

  it("uses render props with validation visibility flag semantics", () => {
    render(
      <FieldErrorRoot>
        {(state) => (
          <span data-invalid={String(Boolean(state?.isInvalid))}>
            {state?.validationDetails ? "Multiple issues detected" : "Fix the highlighted fields"}
          </span>
        )}
      </FieldErrorRoot>,
    );
    expect(screen.getByText(/multiple issues detected|fix the highlighted fields/i)).toBeTruthy();
  });

  it("surfaces URL scheme validation for webhook endpoints", () => {
    render(
      <FieldErrorRoot id="webhook-url-err">
        Webhook URL must use https and respond with HTTP 200 within 5 seconds.
      </FieldErrorRoot>,
    );
    expect(screen.getByText(/https/i)).toBeTruthy();
    expect(screen.getByText(/HTTP 200/i)).toBeTruthy();
  });
});
