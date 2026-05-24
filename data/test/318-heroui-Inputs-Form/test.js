import React from "react";
import {fireEvent, render, screen} from "@testing-library/react";

import {FormRoot} from "./source";

describe("Heroui FormRoot (data_test fixture)", () => {
  it("renders a native form element", () => {
    const {container} = render(
      <FormRoot aria-label="profile-form">
        <input defaultValue="demo" name="note" />
      </FormRoot>,
    );
    const form = container.querySelector("form");
    expect(form).toBeTruthy();
    expect(form?.getAttribute("aria-label")).toBe("profile-form");
  });

  it("runs onSubmit when the user submits", () => {
    let submitted = false;
    render(
      <FormRoot
        onSubmit={(e) => {
          e.preventDefault();
          submitted = true;
        }}
      >
        <button type="submit">Save</button>
      </FormRoot>,
    );
    fireEvent.click(screen.getByRole("button", {name: /save/i}));
    expect(submitted).toBe(true);
  });

  it("fires onReset when the user clears the form", () => {
    let resets = 0;
    render(
      <FormRoot onReset={() => (resets += 1)}>
        <input name="title" defaultValue="draft" />
        <button type="reset">Clear form</button>
      </FormRoot>,
    );
    fireEvent.click(screen.getByRole("button", {name: /clear form/i}));
    expect(resets).toBe(1);
  });

  it("supports GET action and query-style submission fields", () => {
    const {container} = render(
      <FormRoot action="/search" method="get" autoComplete="off">
        <input name="q" defaultValue="heroui" aria-label="Search query" />
        <button type="submit">Search</button>
      </FormRoot>,
    );
    const form = container.querySelector("form");
    expect(form?.getAttribute("method")).toBe("get");
    expect(form?.getAttribute("action")).toBe("/search");
    expect(form?.getAttribute("autoComplete")).toBe("off");
  });

  it("allows multipart encoding for file uploads", () => {
    const {container} = render(
      <FormRoot encType="multipart/form-data" noValidate>
        <input name="avatar" type="file" aria-label="Avatar file" />
        <button type="submit">Upload</button>
      </FormRoot>,
    );
    const form = container.querySelector("form");
    expect(form?.getAttribute("enctype")).toBe("multipart/form-data");
    expect(form?.hasAttribute("noValidate")).toBe(true);
  });

  it("handles onInvalid when a control fails constraint validation", () => {
    let invalidEvents = 0;
    render(
      <FormRoot onInvalid={() => (invalidEvents += 1)}>
        <input name="email" type="email" required aria-label="Work email" />
        <button type="submit">Validate</button>
      </FormRoot>,
    );
    const input = screen.getByRole("textbox", {name: /work email/i});
    fireEvent.invalid(input);
    expect(invalidEvents).toBe(1);
  });

  it("groups inputs with fieldset and legend for accessibility", () => {
    render(
      <FormRoot aria-label="billing">
        <fieldset>
          <legend>Payment method</legend>
          <label>
            <input type="radio" name="pay" value="card" defaultChecked /> Card
          </label>
          <label>
            <input type="radio" name="pay" value="ach" /> ACH transfer
          </label>
        </fieldset>
        <button type="submit">Continue</button>
      </FormRoot>,
    );
    expect(screen.getByText("Payment method")).toBeTruthy();
    expect(screen.getByText("ACH transfer")).toBeTruthy();
  });

  it("applies custom className and data attributes on the form", () => {
    const {container} = render(
      <FormRoot className="rounded-md border p-4" data-testid="signup-shell">
        <input name="username" autoComplete="username" />
      </FormRoot>,
    );
    const form = container.querySelector("form");
    expect(form?.className).toContain("rounded-md");
    expect(container.querySelector('[data-testid="signup-shell"]')).toBeTruthy();
  });

  it("supports controlled text input updates before submit", () => {
    function ControlledSnippet() {
      const [bio, setBio] = React.useState("");
      return (
        <FormRoot
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <textarea
            aria-label="Biography"
            name="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={280}
          />
          <button type="submit">Publish profile</button>
        </FormRoot>
      );
    }
    render(<ControlledSnippet />);
    const area = screen.getByRole("textbox", {name: /biography/i});
    fireEvent.change(area, {target: {value: "Ships metamorphic tests with confidence."}});
    expect(area).toHaveValue("Ships metamorphic tests with confidence.");
    fireEvent.click(screen.getByRole("button", {name: /publish profile/i}));
  });
});
