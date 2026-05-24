import React from "react";
import {render, screen} from "@testing-library/react";

import {DescriptionRoot} from "./source";

describe("Heroui DescriptionRoot (data_test fixture)", () => {
  it("renders helper description text", () => {
    render(
      <DescriptionRoot id="pw-hint">
        Use at least 8 characters, including a number and a symbol.
      </DescriptionRoot>,
    );
    expect(screen.getByText(/8 characters/i)).toBeTruthy();
    expect(screen.getByText(/number and a symbol/i)).toBeTruthy();
  });

  it("exposes the provided id on the host node", () => {
    const {container} = render(<DescriptionRoot id="field-desc">Visible caption</DescriptionRoot>);
    const node = container.querySelector("#field-desc");
    expect(node).toBeTruthy();
    expect(node?.textContent).toContain("Visible caption");
  });

  it("supports supplementary aria details for screen readers", () => {
    render(
      <DescriptionRoot id="price-footnote" aria-live="polite">
        Price includes estimated tax; final charge may differ at checkout.
      </DescriptionRoot>,
    );
    const el = document.getElementById("price-footnote");
    expect(el?.getAttribute("aria-live")).toBe("polite");
    expect(screen.getByText(/estimated tax/i)).toBeTruthy();
  });

  it("applies className for muted secondary copy", () => {
    const {container} = render(
      <DescriptionRoot className="text-sm text-muted-foreground">
        Optional — we never sell your email address.
      </DescriptionRoot>,
    );
    expect(container.textContent).toMatch(/optional/i);
    expect(container.querySelector(".text-sm")).toBeTruthy();
  });

  it("renders long policy copy with line breaks", () => {
    render(
      <DescriptionRoot id="consent-copy">
        By continuing you agree to the Terms of Service and acknowledge the Privacy Policy,
        including data processing in your region and the right to withdraw consent.
      </DescriptionRoot>,
    );
    expect(screen.getByText(/terms of service/i)).toBeTruthy();
    expect(screen.getByText(/privacy policy/i)).toBeTruthy();
    expect(screen.getByText(/withdraw consent/i)).toBeTruthy();
  });

  it("can describe validation constraints next to a control", () => {
    render(
      <DescriptionRoot slot="description" id="slug-rules">
        Slug must be lowercase letters, digits, or hyphen; max length 64 characters.
      </DescriptionRoot>,
    );
    expect(screen.getByText(/lowercase letters/i)).toBeTruthy();
    expect(screen.getByText(/max length 64/i)).toBeTruthy();
  });

  it("supports numeric formatting hints", () => {
    render(
      <DescriptionRoot id="amount-hint">Enter amount using two decimal places (e.g. 19.99).</DescriptionRoot>,
    );
    expect(screen.getByText(/two decimal/i)).toBeTruthy();
    expect(screen.getByText(/19\.99/)).toBeTruthy();
  });

  it("combines id and className for design system documentation blocks", () => {
    const {container} = render(
      <DescriptionRoot id="ds-caption" className="max-w-prose leading-relaxed">
        This field is powered by react-aria Text and inherits HeroUI description tokens.
      </DescriptionRoot>,
    );
    expect(container.querySelector("#ds-caption")?.className).toContain("max-w-prose");
    expect(screen.getByText(/react-aria text/i)).toBeTruthy();
  });
});
