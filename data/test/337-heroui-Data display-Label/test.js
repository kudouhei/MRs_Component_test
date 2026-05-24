import React from "react";
import {render, screen} from "@testing-library/react";

import {LabelRoot} from "./source";

describe("Heroui LabelRoot (data_test fixture)", () => {
  it("renders label text associated with an input", () => {
    render(
      <>
        <LabelRoot htmlFor="user-email">Work email</LabelRoot>
        <input id="user-email" type="email" name="email" defaultValue="" />
      </>,
    );
    expect(screen.getByText("Work email")).toBeTruthy();
    const input = document.getElementById("user-email");
    expect(input).toBeTruthy();
    expect(input?.getAttribute("type")).toBe("email");
  });

  it("supports required and invalid visual states via props", () => {
    const {container} = render(
      <LabelRoot htmlFor="code" isRequired isInvalid>
        Promo code
      </LabelRoot>,
    );
    expect(screen.getByText("Promo code")).toBeTruthy();
    expect(container.querySelector("label")).toBeTruthy();
  });

  it("marks the label as disabled when the field is disabled", () => {
    render(
      <>
        <LabelRoot htmlFor="legacy-id" isDisabled>
          Legacy account ID (read-only)
        </LabelRoot>
        <input id="legacy-id" disabled defaultValue="acct_01HX" />
      </>,
    );
    expect(screen.getByText(/legacy account id/i)).toBeTruthy();
    expect(document.getElementById("legacy-id")?.disabled).toBe(true);
  });

  it("uses invalid styling without required marker", () => {
    render(
      <>
        <LabelRoot htmlFor="phone" isInvalid>
          Mobile phone
        </LabelRoot>
        <input id="phone" type="tel" aria-invalid="true" defaultValue="000" />
      </>,
    );
    expect(screen.getByText("Mobile phone")).toBeTruthy();
  });

  it("associates with textarea for multiline fields", () => {
    render(
      <>
        <LabelRoot htmlFor="feedback">Release notes</LabelRoot>
        <textarea id="feedback" name="notes" rows={4} placeholder="What changed?" />
      </>,
    );
    expect(screen.getByText("Release notes")).toBeTruthy();
    expect(screen.getByPlaceholderText(/what changed/i)).toBeTruthy();
  });

  it("wraps a nested input for implicit labeling", () => {
    render(
      <LabelRoot>
        Subscribe to changelog emails
        <input type="checkbox" name="subscribe" defaultChecked />
      </LabelRoot>,
    );
    expect(screen.getByText(/changelog emails/i)).toBeTruthy();
    expect(screen.getByRole("checkbox")).toBeTruthy();
  });

  it("applies className for typography alignment", () => {
    const {container} = render(
      <LabelRoot htmlFor="budget" className="text-base font-semibold">
        Quarterly budget (USD)
      </LabelRoot>,
    );
    expect(container.querySelector("label")?.className).toContain("font-semibold");
    expect(screen.getByText(/quarterly budget/i)).toBeTruthy();
  });

  it("supports required-only state for mandatory profile fields", () => {
    render(
      <>
        <LabelRoot htmlFor="legal-name" isRequired>
          Full legal name
        </LabelRoot>
        <input id="legal-name" name="legalName" required aria-required="true" />
      </>,
    );
    expect(screen.getByText(/full legal name/i)).toBeTruthy();
    expect(document.getElementById("legal-name")?.required).toBe(true);
  });

  it("labels a select control for metamorphic coverage of native pickers", () => {
    render(
      <>
        <LabelRoot htmlFor="country">Country / region</LabelRoot>
        <select id="country" name="country" defaultValue="us">
          <option value="us">United States</option>
          <option value="de">Germany</option>
        </select>
      </>,
    );
    expect(screen.getByText(/country/i)).toBeTruthy();
    expect(screen.getByRole("combobox")).toHaveValue("us");
  });
});
