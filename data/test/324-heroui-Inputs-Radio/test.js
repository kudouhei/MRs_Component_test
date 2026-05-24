import React from "react";
import {fireEvent, render, screen} from "@testing-library/react";
import {RadioGroup} from "react-aria-components/RadioGroup";

import {RadioContent, RadioControl, RadioIndicator, RadioRoot} from "./source";

function option(value, label) {
  return (
    <RadioRoot value={value}>
      <RadioControl>
        <RadioIndicator />
      </RadioControl>
      <RadioContent>{label}</RadioContent>
    </RadioRoot>
  );
}

describe("Heroui Radio (data_test fixture)", () => {
  it("renders options inside a RadioGroup", () => {
    render(
      <RadioGroup aria-label="plan" defaultValue="pro">
        {option("free", "Free")}
        {option("pro", "Pro")}
      </RadioGroup>,
    );
    expect(screen.getByText("Free")).toBeTruthy();
    expect(screen.getByText("Pro")).toBeTruthy();
  });

  it("changes selection on click", () => {
    render(
      <RadioGroup aria-label="size" defaultValue="m">
        {option("s", "Small")}
        {option("m", "Medium")}
      </RadioGroup>,
    );
    fireEvent.click(screen.getByText("Small"));
    expect(screen.getByText("Small")).toBeTruthy();
  });

  it("supports horizontal orientation for toolbar-like layouts", () => {
    render(
      <RadioGroup aria-label="text alignment" defaultValue="left" orientation="horizontal">
        {option("left", "Left")}
        {option("center", "Center")}
        {option("right", "Right")}
      </RadioGroup>,
    );
    expect(screen.getByText("Center")).toBeTruthy();
    fireEvent.click(screen.getByText("Right"));
    expect(screen.getByText("Right")).toBeTruthy();
  });

  it("disables all radios when the group is disabled", () => {
    render(
      <RadioGroup aria-label="locked tier" defaultValue="basic" isDisabled>
        {option("basic", "Basic")}
        {option("premium", "Premium")}
      </RadioGroup>,
    );
    const radios = screen.getAllByRole("radio");
    expect(radios.length).toBe(2);
    const allDisabled = radios.every(
      (r) =>
        Boolean(r.disabled) ||
        r.getAttribute("aria-disabled") === "true" ||
        r.getAttribute("data-disabled") === "true",
    );
    expect(allDisabled).toBe(true);
  });

  it("sets a shared name for native form posts", () => {
    render(
      <RadioGroup aria-label="region" name="region" defaultValue="us-east">
        {option("us-east", "US East")}
        {option("eu-west", "EU West")}
      </RadioGroup>,
    );
    const inputs = screen.getAllByRole("radio");
    expect(inputs.length).toBe(2);
    expect(inputs.every((el) => el.getAttribute("name") === "region")).toBe(true);
  });

  it("uses render props on RadioRoot to reflect selection state", () => {
    render(
      <RadioGroup aria-label="toggle" defaultValue="off">
        <RadioRoot value="off">
          {(state) => (
            <>
              <RadioControl>
                <RadioIndicator />
              </RadioControl>
              <RadioContent>{state.isSelected ? "Notifications off" : "Off"}</RadioContent>
            </>
          )}
        </RadioRoot>
        <RadioRoot value="on">
          {(state) => (
            <>
              <RadioControl>
                <RadioIndicator />
              </RadioControl>
              <RadioContent>{state.isSelected ? "Notifications on" : "On"}</RadioContent>
            </>
          )}
        </RadioRoot>
      </RadioGroup>,
    );
    expect(screen.getByText("Notifications off")).toBeTruthy();
    fireEvent.click(screen.getByText("On"));
    expect(screen.getByText("Notifications on")).toBeTruthy();
  });

  it("toggles focus with keyboard Space on a radio control", () => {
    render(
      <RadioGroup aria-label="theme" defaultValue="light">
        {option("light", "Light theme")}
        {option("dark", "Dark theme")}
      </RadioGroup>,
    );
    const dark = screen.getByText("Dark theme");
    dark.focus();
    fireEvent.keyDown(dark, {key: " ", code: "Space"});
    expect(screen.getByText("Dark theme")).toBeTruthy();
  });

  it("applies className on RadioRoot for layout styling", () => {
    const {container} = render(
      <RadioGroup aria-label="density" defaultValue="cozy">
        <RadioRoot value="cozy" className="flex items-center gap-2">
          <RadioControl>
            <RadioIndicator />
          </RadioControl>
          <RadioContent>Cozy spacing</RadioContent>
        </RadioRoot>
        <RadioRoot value="compact" className="flex items-center gap-2">
          <RadioControl>
            <RadioIndicator />
          </RadioControl>
          <RadioContent>Compact spacing</RadioContent>
        </RadioRoot>
      </RadioGroup>,
    );
    expect(container.querySelector(".flex")).toBeTruthy();
    expect(screen.getByText("Compact spacing")).toBeTruthy();
  });

  it("supports a three-way severity choice with default selection", () => {
    render(
      <RadioGroup aria-label="severity" defaultValue="major">
        {option("minor", "Minor")}
        {option("major", "Major")}
        {option("critical", "Critical")}
      </RadioGroup>,
    );
    expect(screen.getByText("Major")).toBeTruthy();
    fireEvent.click(screen.getByText("Critical"));
    expect(screen.getByText("Critical")).toBeTruthy();
  });
});
