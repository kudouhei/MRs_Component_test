// ---- packages/react/src/slider/control/SliderControl.test.tsx ----
import { expect } from 'vitest';
import { screen } from '@mui/internal-test-utils';
import { Slider } from '@base-ui/react/slider';
import { createRenderer, describeConformance } from '#test-utils';

describe('<Slider.Control />', () => {
  const { render } = createRenderer();

  describeConformance(<Slider.Control />, () => ({
    render: (node) => {
      return render(<Slider.Root>{node}</Slider.Root>);
    },
    refInstanceof: window.HTMLDivElement,
  }));

  it('does not apply a tabIndex by default', async () => {
    await render(
      <Slider.Root defaultValue={50}>
        <Slider.Control data-testid="control">
          <Slider.Thumb />
        </Slider.Control>
      </Slider.Root>,
    );

    expect(screen.getByTestId('control')).not.toHaveAttribute('tabindex');
  });
});

// ---- packages/react/src/slider/indicator/SliderIndicator.test.tsx ----
import { Slider } from '@base-ui/react/slider';
import { createRenderer, describeConformance } from '#test-utils';

describe('<Slider.Indicator />', () => {
  const { render } = createRenderer();

  describeConformance(<Slider.Indicator />, () => ({
    render: (node) => {
      return render(<Slider.Root>{node}</Slider.Root>);
    },
    refInstanceof: window.HTMLDivElement,
  }));
});

// ---- packages/react/src/slider/label/SliderLabel.test.tsx ----
import { Slider } from '@base-ui/react/slider';
import { createRenderer, describeConformance } from '#test-utils';

describe('<Slider.Label />', () => {
  const { render } = createRenderer();

  describeConformance(<Slider.Label />, () => ({
    refInstanceof: window.HTMLDivElement,
    render(node) {
      return render(
        <Slider.Root defaultValue={50}>
          {node}
          <Slider.Control>
            <Slider.Thumb />
          </Slider.Control>
        </Slider.Root>,
      );
    },
  }));
});

// ---- packages/react/src/slider/root/SliderRoot.test.tsx ----
import { expect, expect as expectVitest, vi } from 'vitest';
import * as React from 'react';
import { act, flushMicrotasks, fireEvent, screen, waitFor } from '@mui/internal-test-utils';
import { DirectionProvider, type TextDirection } from '@base-ui/react/direction-provider';
import { Field } from '@base-ui/react/field';
import { Slider } from '@base-ui/react/slider';
import { Form } from '@base-ui/react/form';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';
import { isWebKit } from '@base-ui/utils/detectBrowser';
import { REASONS } from '../../internals/reasons';
import {
  ARROW_RIGHT,
  ARROW_LEFT,
  ARROW_UP,
  ARROW_DOWN,
  HOME,
  END,
} from '../../internals/composite/composite';
import type { Orientation } from '../../internals/types';
import type { SliderRoot } from './SliderRoot';
import { createTouches, getHorizontalSliderRect } from '../utils/test-utils';

const USD_NUMBER_FORMAT: Intl.NumberFormatOptions = {
  style: 'currency',
  currency: 'USD',
};

function TestSlider(props: SliderRoot.Props) {
  return (
    <Slider.Root data-testid="root" {...props}>
      <Slider.Value data-testid="value" />
      <Slider.Control data-testid="control">
        <Slider.Track>
          <Slider.Indicator />
          <Slider.Thumb data-testid="thumb" />
        </Slider.Track>
      </Slider.Control>
    </Slider.Root>
  );
}

function TestRangeSlider(props: SliderRoot.Props) {
  return (
    <Slider.Root data-testid="root" {...props}>
      <Slider.Value data-testid="value" />
      <Slider.Control data-testid="control">
        <Slider.Track>
          <Slider.Indicator />
          <Slider.Thumb index={0} data-testid="thumb" />
          <Slider.Thumb index={1} data-testid="thumb" />
        </Slider.Track>
      </Slider.Control>
    </Slider.Root>
  );
}

function TestMultiThumbSlider(props: SliderRoot.Props) {
  return (
    <Slider.Root data-testid="root" {...props}>
      <Slider.Value data-testid="value" />
      <Slider.Control data-testid="control">
        <Slider.Track>
          <Slider.Indicator />
          <Slider.Thumb index={0} data-testid="thumb" />
          <Slider.Thumb index={1} data-testid="thumb" />
          <Slider.Thumb index={2} data-testid="thumb" />
        </Slider.Track>
      </Slider.Control>
    </Slider.Root>
  );
}

describe.skipIf(typeof Touch === 'undefined')('<Slider.Root />', () => {
  beforeAll(function beforeHook() {
    // PointerEvent not fully implemented in jsdom, causing
    // fireEvent.pointer* to ignore options
    // https://github.com/jsdom/jsdom/issues/2527
    (window as any).PointerEvent = window.MouseEvent;
  });

  const { render, renderToString } = createRenderer();

  describeConformance(<Slider.Root defaultValue={50} />, () => ({
    render,
    refInstanceof: window.HTMLDivElement,
  }));

  describe('server-side rendering', () => {
    it('does not link Slider.Label before hydration', () => {
      renderToString(
        <Slider.Root defaultValue={30} data-testid="root">
          <Slider.Label data-testid="label">Volume</Slider.Label>
          <Slider.Control>
            <Slider.Track>
              <Slider.Thumb />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      const root = screen.getByTestId('root');
      const label = screen.getByTestId('label');
      const slider = screen.getByRole('slider');

      expect(label.id).not.toBe('');
      expect(root.id).not.toBe('');
      expect(root).not.toHaveAttribute('aria-labelledby');
      expect(slider).not.toHaveAttribute('aria-labelledby');
    });
  });

  it.skipIf(isWebKit)('should not break when initial value is out of range', async () => {
    await render(<TestRangeSlider value={[19, 41]} min={20} max={40} />);

    const sliderControl = screen.getByTestId('control');

    vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

    fireEvent.touchStart(
      sliderControl,
      createTouches([{ identifier: 1, clientX: 100, clientY: 0 }]),
    );

    fireEvent.touchMove(document.body, createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]));
  });

  describe('ARIA attributes', () => {
    it('it has the correct aria attributes', async () => {
      await render(
        <Slider.Root defaultValue={30} aria-labelledby="labelId" data-testid="root">
          <Slider.Value />
          <Slider.Control>
            <Slider.Track>
              <Slider.Indicator />
              <Slider.Thumb />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      const root = screen.getByTestId('root');
      const slider = screen.getByRole('slider');

      expect(slider.tagName).toBe('INPUT');

      expect(root).toHaveAttribute('aria-labelledby', 'labelId');

      expect(slider).toHaveAttribute('aria-valuenow', '30');
      expect(slider).toHaveAttribute('aria-orientation', 'horizontal');
      expect(slider).toHaveAttribute('aria-labelledby', 'labelId');
      expect(slider).toHaveAttribute('step', '1');
    });

    it('should update aria-valuenow', async () => {
      await render(<TestSlider defaultValue={50} />);
      const slider = screen.getByRole('slider');

      await act(async () => {
        slider.focus();
      });

      fireEvent.change(slider, { target: { value: '51' } });
      expect(slider).toHaveAttribute('aria-valuenow', '51');

      fireEvent.keyDown(slider, { key: ARROW_RIGHT });
      expect(slider).toHaveAttribute('aria-valuenow', '52');
    });

    it('should set default aria-valuetext on range slider thumbs', async () => {
      await render(<TestRangeSlider defaultValue={[44, 50]} />);

      const [thumb1, thumb2] = screen.getAllByTestId('thumb');

      expect(thumb1.querySelector('input')).toHaveAttribute('aria-valuetext', '44 start range');
      expect(thumb2.querySelector('input')).toHaveAttribute('aria-valuetext', '50 end range');
    });
  });

  describe.skipIf(isJSDOM || isWebKit)('rtl', () => {
    it('should handle RTL', async () => {
      const handleValueChange = vi.fn((newValue) => newValue);

      await render(
        <div dir="rtl">
          <DirectionProvider direction="rtl">
            <TestSlider value={30} onValueChange={handleValueChange} />
          </DirectionProvider>
        </div>,
      );

      const sliderControl = screen.getByTestId('control');
      const sliderThumb = screen.getByTestId('thumb');
      expect(sliderThumb.style.insetInlineStart).toBe('30%');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 22, clientY: 0 }]),
      );

      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueChange.mock.results[0]?.value).toBe(80);
      expect(handleValueChange.mock.results.at(-1)?.value).toBe(78);
    });
  });

  describe('prop: disabled', () => {
    it('should render data-disabled on all subcomponents', async () => {
      await render(
        <Slider.Root defaultValue={30} disabled data-testid="root">
          <Slider.Value data-testid="value" />
          <Slider.Control data-testid="control">
            <Slider.Track data-testid="track">
              <Slider.Indicator data-testid="indicator" />
              <Slider.Thumb data-testid="thumb" />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      const root = screen.getByTestId('root');
      const value = screen.getByTestId('value');
      const control = screen.getByTestId('control');
      const track = screen.getByTestId('track');
      const indicator = screen.getByTestId('indicator');
      const thumb = screen.getByTestId('thumb');

      [root, value, control, track, indicator, thumb].forEach((subcomponent) => {
        expect(subcomponent).toHaveAttribute('data-disabled', '');
      });
    });

    // TODO: Don't skip once a fix for https://github.com/jsdom/jsdom/issues/3029 is released.
    it.skipIf(isJSDOM || isWebKit)(
      'should not respond to drag events after becoming disabled',
      async () => {
        const { setProps } = await render(
          <TestSlider defaultValue={0} data-testid="slider-root" />,
        );

        const sliderControl = screen.getByTestId('control');

        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );
        fireEvent.touchStart(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 21, clientY: 0 }]),
        );

        const thumb = screen.getByRole('slider');

        expect(thumb).toHaveAttribute('aria-valuenow', '21');
        expect(thumb).toHaveFocus();

        await setProps({ disabled: true });
        expect(thumb).not.toHaveFocus();
        // expect(thumb).not.toHaveClass(classes.active);

        fireEvent.touchMove(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 30, clientY: 0 }]),
        );

        expect(thumb).toHaveAttribute('aria-valuenow', '21');
      },
    );

    // TODO: Don't skip once a fix for https://github.com/jsdom/jsdom/issues/3029 is released.
    it.skipIf(isJSDOM || isWebKit)('should not respond to drag events if disabled', async () => {
      await render(<TestSlider defaultValue={21} data-testid="slider-root" disabled />);

      const thumb = screen.getByRole('slider');
      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 21, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 30, clientY: 0 }]),
      );

      fireEvent.touchEnd(
        document.body,
        createTouches([{ identifier: 1, clientX: 30, clientY: 0 }]),
      );

      expect(thumb).toHaveAttribute('aria-valuenow', '21');
    });
  });

  describe('prop: orientation', () => {
    it('sets the `aria-orientation` attribute', async () => {
      await render(<TestSlider orientation="vertical" />);

      const sliderRoot = screen.getByRole('slider');
      expect(sliderRoot).toHaveAttribute('aria-orientation', 'vertical');
    });

    it('sets the data-orientation attribute', async () => {
      await render(<TestSlider />);

      const sliderRoot = screen.getByRole('group');
      expect(sliderRoot).toHaveAttribute('data-orientation', 'horizontal');
      const sliderControl = screen.getByTestId('control');
      expect(sliderControl).toHaveAttribute('data-orientation', 'horizontal');
      const sliderOutput = screen.getByTestId('value');
      expect(sliderOutput).toHaveAttribute('data-orientation', 'horizontal');
    });

    it.skipIf(isJSDOM || !/WebKit/.test(window.navigator.userAgent))(
      'does not set the orientation via appearance for WebKit browsers',
      async () => {
        await render(<TestSlider orientation="vertical" />);

        const slider = screen.getByRole('slider');

        expect(slider).toHaveProperty('tagName', 'INPUT');
        expect(slider).toHaveProperty('type', 'range');
        // Only relevant to implementations using `input[type="range"]` with implicit `[role="slider"]`
        // We're not setting this by default because it changes horizontal keyboard navigation in WebKit: https://issues.chromium.org/issues/40739626
        expect(slider).not.toHaveComputedStyle({ webkitAppearance: 'slider-vertical' });
      },
    );

    it.skipIf(isJSDOM || isWebKit)('should report the right position', async () => {
      const handleValueChange = vi.fn();

      await render(
        <TestSlider orientation="vertical" defaultValue={20} onValueChange={handleValueChange} />,
      );

      const sliderControl = screen.getByTestId('control');
      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() => ({
        width: 10,
        height: 100,
        bottom: 100,
        left: 0,
        x: 0,
        y: 0,
        top: 0,
        right: 10,
        toJSON() {},
      }));

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 0, clientY: 20 }]),
      );
      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 0, clientY: 22 }]),
      );

      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueChange.mock.calls[0][0]).toBe(80);
      expect(handleValueChange.mock.calls[1][0]).toBe(78);
    });
  });

  describe('prop: step', () => {
    it('supports non-integer values', async () => {
      await render(
        <React.Fragment>
          <TestSlider value={51.1} min={-100} max={100} step={0.00000001} />
          <TestSlider value={0.00000005} min={-100} max={100} step={0.00000001} />
          <TestSlider value={1e-7} min={-100} max={100} step={0.00000001} />
        </React.Fragment>,
      );
      const [slider1, slider2, slider3] = screen.getAllByRole('slider');

      expect(slider1).toHaveAttribute('aria-valuenow', '51.1');
      expect(slider2).toHaveAttribute('aria-valuenow', '5e-8');
      expect(slider3).toHaveAttribute('aria-valuenow', '1e-7');
    });

    it.skipIf(isJSDOM || isWebKit)('should round value to step precision', async () => {
      await render(<TestSlider defaultValue={0.2} min={0} max={1} step={0.1} />);

      const slider = screen.getByRole('slider');

      await act(async () => {
        slider.focus();
      });

      const sliderControl = screen.getByTestId('control');
      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      await act(async () => {
        slider.focus();
      });

      expect(slider).toHaveAttribute('aria-valuenow', '0.2');

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 80, clientY: 0 }]),
      );
      expect(slider).toHaveAttribute('aria-valuenow', '0.8');

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 40, clientY: 0 }]),
      );
      expect(slider).toHaveAttribute('aria-valuenow', '0.4');
    });

    it.skipIf(isJSDOM || isWebKit)(
      'should not fail to round value to step precision when step is very small',
      async () => {
        await render(
          <TestSlider defaultValue={0.00000002} min={0} max={0.0000001} step={0.00000001} />,
        );

        const slider = screen.getByRole('slider');

        await act(async () => {
          slider.focus();
        });

        const sliderControl = screen.getByTestId('control');
        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        await act(async () => {
          slider.focus();
        });

        expect(slider).toHaveAttribute('aria-valuenow', '2e-8');

        fireEvent.touchStart(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
        );

        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 80, clientY: 0 }]),
        );
        expect(slider).toHaveAttribute('aria-valuenow', '8e-8');
      },
    );

    it.skipIf(isJSDOM || isWebKit)(
      'should not fail to round value to step precision when step is very small and negative',
      async () => {
        await render(
          <TestSlider defaultValue={-0.00000002} min={-0.0000001} max={0} step={0.00000001} />,
        );

        const slider = screen.getByRole('slider');

        await act(async () => {
          slider.focus();
        });

        const sliderControl = screen.getByTestId('control');
        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        await act(async () => {
          slider.focus();
        });

        expect(slider).toHaveAttribute('aria-valuenow', '-2e-8');

        fireEvent.touchStart(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 80, clientY: 0 }]),
        );

        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
        );
        expect(slider).toHaveAttribute('aria-valuenow', '-8e-8');
      },
    );
  });

  describe('prop: max', () => {
    it('sets the max attribute on the input', async () => {
      await render(<TestSlider defaultValue={150} step={100} max={750} />);
      expect(screen.getByRole('slider')).toHaveAttribute('max', '750');
    });

    it('should not go more than the max', async () => {
      const { user } = await render(<TestSlider defaultValue={100} step={100} max={200} />);

      const slider = screen.getByRole('slider');

      await user.keyboard('[Tab]');

      await user.keyboard(`[${ARROW_RIGHT}]`);
      expect(slider).toHaveAttribute('aria-valuenow', '200');
      await user.keyboard(`[${ARROW_RIGHT}]`);
      expect(slider).toHaveAttribute('aria-valuenow', '200');
    });

    it.skipIf(isJSDOM || isWebKit)('should reach right edge value', async () => {
      await render(<TestSlider defaultValue={90} min={6} max={108} step={10} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      const slider = screen.getByRole('slider');
      await act(async () => {
        slider.focus();
      });

      expect(slider).toHaveAttribute('aria-valuenow', '90');

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 100, clientY: 0 }]),
      );
      expect(slider).toHaveAttribute('aria-valuenow', '106');

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
      );
      expect(slider).toHaveAttribute('aria-valuenow', '106');

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 50, clientY: 0 }]),
      );
      expect(slider).toHaveAttribute('aria-valuenow', '56');

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: -100, clientY: 0 }]),
      );
      expect(slider).toHaveAttribute('aria-valuenow', '6');
    });
  });

  describe('prop: min', () => {
    it('sets the min attribute on the input', async () => {
      await render(<TestSlider defaultValue={150} step={100} min={150} max={200} />);
      expect(screen.getByRole('slider')).toHaveAttribute('min', '150');
    });

    it('should use min as the step origin', async () => {
      await render(<TestSlider defaultValue={150} step={100} max={750} min={150} />);

      const slider = screen.getByRole('slider');
      await act(async () => {
        slider.focus();
      });

      expect(slider).toHaveAttribute('aria-valuenow', '150');
    });

    it('should not go less than the min', async () => {
      const { user } = await render(<TestSlider defaultValue={1} step={1} min={0} />);
      const slider = screen.getByRole('slider');

      await user.keyboard('[Tab]');

      await user.keyboard(`[${ARROW_LEFT}]`);
      expect(slider).toHaveAttribute('aria-valuenow', '0');
      await user.keyboard(`[${ARROW_LEFT}]`);
      expect(slider).toHaveAttribute('aria-valuenow', '0');
    });
  });

  describe('prop: minStepsBetweenValues', () => {
    it('should enforce a minimum difference between range slider values', async () => {
      const handleValueChange = vi.fn();

      const { user } = await render(
        <TestRangeSlider
          onValueChange={handleValueChange}
          defaultValue={[44, 50]}
          step={2}
          minStepsBetweenValues={2}
        />,
      );

      await user.keyboard('[Tab]');

      await user.keyboard(`[${ARROW_UP}]`);
      expect(handleValueChange.mock.calls.length).toBe(1);
      expect(handleValueChange.mock.calls[0][0]).toEqual([46, 50]);
      await user.keyboard(`[${ARROW_UP}]`);
      expect(handleValueChange.mock.calls.length).toBe(1);

      await user.keyboard('[Tab]');

      await user.keyboard(`[${ARROW_UP}]`);
      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueChange.mock.calls[1][0]).toEqual([46, 52]);
      await user.keyboard(`[${ARROW_DOWN}]`);
      await user.keyboard(`[${ARROW_DOWN}]`);
      expect(handleValueChange.mock.calls.length).toBe(3);
      expect(handleValueChange.mock.calls[2][0]).toEqual([46, 50]);
    });
  });

  describe('prop: onValueCommitted', () => {
    it('single value', async () => {
      const handleValueCommitted = vi.fn((newValue: number, eventDetails) => ({
        newValue,
        reason: eventDetails.reason,
      }));

      await render(
        <Slider.Root onValueCommitted={handleValueCommitted} defaultValue={0}>
          <Slider.Control data-testid="control">
            <Slider.Thumb />
          </Slider.Control>
        </Slider.Root>,
      );

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      const slider = screen.getByRole('slider');

      fireEvent.pointerDown(sliderControl, {
        buttons: 1,
        clientX: 10,
      });
      fireEvent.pointerUp(sliderControl, {
        buttons: 1,
        clientX: 10,
      });

      expect(handleValueCommitted.mock.calls.length).toBe(1);
      expect(handleValueCommitted.mock.results.at(-1)?.value.newValue).toBe(10);
      expect(handleValueCommitted.mock.results.at(-1)?.value.reason).toBe(REASONS.trackPress);

      await act(async () => {
        slider.focus();
      });

      fireEvent.change(slider, { target: { value: 23 } });
      expect(handleValueCommitted.mock.calls.length).toBe(2);
      expect(handleValueCommitted.mock.results.at(-1)?.value.reason).toBe(REASONS.inputChange);
    });

    it('array value', async () => {
      const handleValueCommitted = vi.fn((newValue: number[], eventDetails) => ({
        newValue,
        reason: eventDetails.reason,
      }));

      await render(
        <Slider.Root onValueCommitted={handleValueCommitted} defaultValue={[10, 20]}>
          <Slider.Control data-testid="control">
            <Slider.Thumb index={0} />
            <Slider.Thumb index={1} />
          </Slider.Control>
        </Slider.Root>,
      );

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      const [thumb1, thumb2] = screen.getAllByRole('slider');

      fireEvent.pointerDown(thumb2, {
        buttons: 1,
        clientX: 20,
      });

      fireEvent.pointerMove(thumb2, {
        buttons: 1,
        clientX: 30,
      });

      expect(handleValueCommitted.mock.calls.length).toBe(0);

      fireEvent.pointerUp(thumb2, {
        buttons: 1,
        clientX: 30,
      });

      expect(handleValueCommitted.mock.calls.length).toBe(1);
      expect(handleValueCommitted.mock.results.at(-1)?.value.reason).toBe(REASONS.drag);

      await act(async () => {
        thumb1.focus();
      });

      fireEvent.change(thumb1, { target: { value: 23 } });
      expect(handleValueCommitted.mock.calls.length).toBe(2);
      expect(handleValueCommitted.mock.results.at(-1)?.value.reason).toBe(REASONS.inputChange);
    });
  });

  describe('events', () => {
    it.skipIf(isJSDOM)('should call handlers', async () => {
      const handleValueChange = vi.fn();
      const handleValueCommitted = vi.fn();

      await render(
        <TestSlider
          onValueChange={handleValueChange}
          onValueCommitted={handleValueCommitted}
          value={0}
        />,
      );

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      const slider = screen.getByRole('slider');

      fireEvent.pointerDown(sliderControl, {
        buttons: 1,
        clientX: 10,
      });
      fireEvent.pointerUp(sliderControl, {
        buttons: 1,
        clientX: 10,
      });

      expect(handleValueChange.mock.calls.length).toBe(1);
      expect(handleValueChange.mock.calls[0][0]).toBe(10);
      expect(handleValueChange.mock.calls[0][1].activeThumbIndex).toBe(0);
      expect(handleValueCommitted.mock.calls.length).toBe(1);
      expect(handleValueCommitted.mock.calls[0][0]).toBe(10);
      expect(handleValueCommitted.mock.calls[0][1].reason).toBe(REASONS.trackPress);

      await act(async () => {
        slider.focus();
      });

      fireEvent.change(slider, { target: { value: 23 } });
      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueCommitted.mock.calls.length).toBe(2);
      expect(handleValueCommitted.mock.calls[1][1].reason).toBe(REASONS.inputChange);
    });

    it.skipIf(isJSDOM || isWebKit)('should support touch events', async () => {
      const handleValueChange = vi.fn();

      await render(
        <TestRangeSlider
          defaultValue={[20, 30]}
          style={{ width: '100px' }}
          onValueChange={handleValueChange}
        />,
      );

      const sliderControl = screen.getByTestId('control');
      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 21, clientY: 0 }]),
      );

      fireEvent.touchEnd(
        document.body,
        createTouches([{ identifier: 1, clientX: 21, clientY: 0 }]),
      );

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 21, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 22, clientY: 0 }]),
      );

      fireEvent.touchEnd(
        document.body,
        createTouches([{ identifier: 1, clientX: 22, clientY: 0 }]),
      );

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 22, clientY: 0 }]),
      );

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 22.1, clientY: 0 }]),
      );

      fireEvent.touchEnd(
        document.body,
        createTouches([{ identifier: 1, clientX: 22.1, clientY: 0 }]),
      );

      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueChange.mock.calls[0][0]).toEqual([21, 30]);
      expect(handleValueChange.mock.calls[1][0]).toEqual([22, 30]);
    });

    it.skipIf(isJSDOM || isWebKit)(
      'should only listen to changes from the same touchpoint',
      async () => {
        const handleValueChange = vi.fn();
        const handleValueCommitted = vi.fn();

        await render(
          <TestSlider
            onValueChange={handleValueChange}
            onValueCommitted={handleValueCommitted}
            value={0}
          />,
        );

        const sliderControl = screen.getByTestId('control');

        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        fireEvent.touchStart(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]),
        );
        expect(handleValueChange.mock.calls.length).toBe(0);
        expect(handleValueCommitted.mock.calls.length).toBe(0);

        fireEvent.touchStart(
          document.body,
          createTouches([{ identifier: 2, clientX: 40, clientY: 0 }]),
        );
        expect(handleValueChange.mock.calls.length).toBe(0);
        expect(handleValueCommitted.mock.calls.length).toBe(0);

        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 1, clientY: 0 }]),
        );
        expect(handleValueChange.mock.calls.length).toBe(1);
        expect(handleValueCommitted.mock.calls.length).toBe(0);

        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 2, clientX: 41, clientY: 0 }]),
        );
        expect(handleValueChange.mock.calls.length).toBe(1);
        expect(handleValueCommitted.mock.calls.length).toBe(0);

        fireEvent.touchEnd(
          document.body,
          createTouches([{ identifier: 1, clientX: 2, clientY: 0 }]),
        );
        expect(handleValueChange.mock.calls.length).toBe(1);
        expect(handleValueCommitted.mock.calls.length).toBe(1);
        expect(handleValueCommitted.mock.calls[0][1].reason).toBe('drag');
      },
    );

    it.skipIf(isJSDOM)('should hedge against a dropped mouseup event', async () => {
      const handleValueChange = vi.fn();

      await render(<TestSlider onValueChange={handleValueChange} value={0} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderControl, {
        buttons: 1,
        clientX: 1,
      });
      expect(handleValueChange.mock.calls.length).toBe(1);
      expect(handleValueChange.mock.calls[0][0]).toBe(1);

      fireEvent.pointerMove(document.body, {
        buttons: 1,
        clientX: 10,
      });
      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueChange.mock.calls[1][0]).toBe(10);

      fireEvent.pointerMove(document.body, {
        buttons: 0,
        clientX: 11,
      });
      // The mouse's button was released, stop the dragging session.
      expect(handleValueChange.mock.calls.length).toBe(2);
    });

    it.skipIf(isWebKit)('should focus the slider when touching', async () => {
      await render(<TestSlider defaultValue={30} />);
      const slider = screen.getByRole('slider');
      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]),
      );

      expect(slider).toHaveFocus();
    });

    it('should focus the slider when dragging', async () => {
      await render(<TestSlider defaultValue={30} step={10} />);
      const slider = screen.getByRole('slider');
      const sliderThumb = screen.getByTestId('thumb');
      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderThumb, {
        buttons: 1,
        clientX: 1,
      });

      await waitFor(() => {
        expect(slider).toHaveFocus();
      });
    });

    it.skipIf(isWebKit)('should not override the event.target on touch events', async () => {
      const handleValueChange = vi.fn();
      const handleNativeEvent = vi.fn();
      const handleEvent = vi.fn();
      function Test() {
        React.useEffect(() => {
          document.addEventListener('touchstart', handleNativeEvent);
          return () => {
            document.removeEventListener('touchstart', handleNativeEvent);
          };
        });

        return (
          <div onTouchStart={handleEvent}>
            <TestSlider value={0} onValueChange={handleValueChange} />
          </div>
        );
      }

      await render(<Test />);
      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]),
      );

      expect(handleValueChange.mock.calls.length).toBe(0);
      expect(handleNativeEvent.mock.calls.length).toBe(1);
      expect(handleNativeEvent.mock.calls[0][0]).toHaveProperty('target', sliderControl);
      expect(handleEvent.mock.calls.length).toBe(1);
      expect(handleEvent.mock.calls[0][0]).toHaveProperty('target', sliderControl);
    });

    it('should not override the event.target on mouse events', async () => {
      const handleValueChange = vi.fn();
      const handleNativeEvent = vi.fn();
      const handleEvent = vi.fn();
      function Test() {
        React.useEffect(() => {
          document.addEventListener('mousedown', handleNativeEvent);
          return () => {
            document.removeEventListener('mousedown', handleNativeEvent);
          };
        });

        return (
          <div onMouseDown={handleEvent}>
            <TestSlider value={0} onValueChange={handleValueChange} />
          </div>
        );
      }
      await render(<Test />);
      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.mouseDown(sliderControl);

      expect(handleValueChange.mock.calls.length).toBe(0);
      expect(handleNativeEvent.mock.calls.length).toBe(1);
      expect(handleNativeEvent.mock.calls[0][0]).toHaveProperty('target', sliderControl);
      expect(handleEvent.mock.calls.length).toBe(1);
      expect(handleEvent.mock.calls[0][0]).toHaveProperty('target', sliderControl);
    });
  });

  describe.skipIf(isWebKit)('dragging state', () => {
    it('should not apply data-dragging for click modality', async () => {
      await render(<TestSlider defaultValue={90} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
      );
      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 21, clientY: 0 }]),
      );
      expect(sliderControl).not.toHaveAttribute('data-dragging');
      fireEvent.touchEnd(document.body, createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]));
    });

    it('should apply data-dragging for dragging modality', async () => {
      await render(<TestSlider defaultValue={90} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.touchStart(
        sliderControl,
        createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
      );
      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
      );
      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
      );

      expect(sliderControl).not.toHaveAttribute('data-dragging');

      fireEvent.touchMove(
        document.body,
        createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
      );

      expect(sliderControl).toHaveAttribute('data-dragging', '');
      fireEvent.touchEnd(document.body, createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]));
      expect(sliderControl).not.toHaveAttribute('data-dragging');
    });
  });

  describe('prop: onValueChange', () => {
    it.skipIf(isJSDOM)('is called when clicking on the control', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={50} onValueChange={handleValueChange} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderControl, {
        buttons: 1,
        clientX: 41,
      });

      expect(handleValueChange.mock.calls.length).toBe(1);
    });

    it('is not called when clicking on the thumb', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={50} onValueChange={handleValueChange} />);

      const sliderControl = screen.getByTestId('control');
      const sliderThumb = screen.getByTestId('thumb');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderThumb, {
        buttons: 1,
        clientX: 51,
      });

      expect(handleValueChange.mock.calls.length).toBe(0);
    });

    it('should not react to right clicks', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={50} onValueChange={handleValueChange} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderControl, {
        button: 2,
        clientX: 41,
      });

      expect(handleValueChange.mock.calls.length).toBe(0);
    });

    it('provides the change reason for input events', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={30} onValueChange={handleValueChange} />);

      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '35' } });

      expect(handleValueChange).toHaveBeenCalledTimes(1);
      const [, details] = handleValueChange.mock.calls[0] as [
        number,
        SliderRoot.ChangeEventDetails,
      ];
      expect(details.reason).toBe(REASONS.inputChange);
      expect(details.activeThumbIndex).toBe(0);
    });

    it('provides the change reason for keyboard interactions', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={40} onValueChange={handleValueChange} />);

      const slider = screen.getByRole('slider');
      await act(async () => {
        slider.focus();
      });
      fireEvent.keyDown(slider, { key: ARROW_RIGHT });

      expect(handleValueChange).toHaveBeenCalledTimes(1);
      const [, details] = handleValueChange.mock.calls[0] as [
        number,
        SliderRoot.ChangeEventDetails,
      ];
      expect(details.reason).toBe('keyboard');
    });

    it.skipIf(isJSDOM || isWebKit)(
      'shows :focus-visible after keyboard interaction following a pointer press',
      async () => {
        await render(<TestSlider defaultValue={40} />);

        const sliderControl = screen.getByTestId('control');
        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        const slider = screen.getByRole('slider');

        fireEvent.pointerDown(sliderControl, {
          pointerId: 1,
          pointerType: 'mouse',
          button: 0,
          buttons: 1,
          clientX: 40,
          clientY: 0,
        });

        await waitFor(() => {
          expect(slider).toHaveFocus();
        });

        expect(slider.matches(':focus-visible')).toBe(false);

        fireEvent.keyDown(slider, { key: ARROW_RIGHT });

        await waitFor(() => {
          expect(slider.matches(':focus-visible')).toBe(true);
        });
      },
    );

    it('provides the change reason for track presses', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={0} onValueChange={handleValueChange} />);

      const sliderControl = screen.getByTestId('control');
      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderControl, {
        pointerId: 1,
        pointerType: 'mouse',
        button: 0,
        buttons: 1,
        clientX: 80,
        clientY: 0,
      });

      await waitFor(() => {
        expect(handleValueChange.mock.calls.length).toBe(1);
      });
      const [, details] = handleValueChange.mock.calls[0] as [
        number | number[],
        SliderRoot.ChangeEventDetails,
      ];
      expect(details.reason).toBe(REASONS.trackPress);
    });

    it.skipIf(isJSDOM)('drags the intended thumb when 3 thumbs are present', async () => {
      const handleValueChange = vi.fn();

      await render(
        <TestMultiThumbSlider
          defaultValue={[10, 40, 60]}
          min={0}
          max={100}
          onValueChange={handleValueChange}
        />,
      );

      const sliderControl = screen.getByTestId('control');
      const thirdThumb = screen.getAllByTestId('thumb')[2];

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);
      vi.spyOn(thirdThumb, 'getBoundingClientRect').mockImplementation(() => ({
        width: 0,
        height: 0,
        bottom: 0,
        left: 60,
        right: 60,
        top: 0,
        x: 60,
        y: 0,
        toJSON() {},
      }));

      fireEvent.pointerDown(thirdThumb, {
        pointerId: 1,
        buttons: 1,
        clientX: 60,
      });

      fireEvent.pointerMove(document, {
        pointerId: 1,
        buttons: 1,
        clientX: 80,
      });

      expect(handleValueChange.mock.calls.length).toBeGreaterThan(0);

      const [newValue] = handleValueChange.mock.lastCall ?? [];
      expect(handleValueChange.mock.lastCall?.[1].activeThumbIndex).toBe(2);
      expect(newValue[0]).toBe(10);
      expect(newValue[1]).toBe(40);
      expect(newValue[2]).not.toBe(60);
    });

    it.skipIf(isJSDOM)('should fire only when the value changes', async () => {
      const handleValueChange = vi.fn();
      await render(<TestSlider defaultValue={20} onValueChange={handleValueChange} />);

      const sliderControl = screen.getByTestId('control');

      vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(getHorizontalSliderRect);

      fireEvent.pointerDown(sliderControl, {
        buttons: 1,
        clientX: 21,
      });

      fireEvent.pointerMove(document.body, {
        buttons: 1,
        clientX: 22,
      });
      // Sometimes another event with the same position is fired by the browser.
      fireEvent.pointerMove(document.body, {
        buttons: 1,
        clientX: 22,
      });

      expect(handleValueChange.mock.calls.length).toBe(2);
      expect(handleValueChange.mock.calls[0][0]).toEqual(21);
      expect(handleValueChange.mock.calls[1][0]).toEqual(22);
    });

    type Values = Array<[string, number[]]>;

    const values = [
      ['readonly range', Object.freeze([2, 1])],
      ['range', [2, 1]],
    ] as Values;
    values.forEach(([valueLabel, value]) => {
      it.skipIf(isJSDOM)(`is called even if the ${valueLabel} did not change`, async () => {
        const handleValueChange = vi.fn();

        await render(
          <TestRangeSlider
            min={0}
            max={5}
            onValueChange={handleValueChange}
            value={value}
            style={{ width: '100px' }}
          />,
        );

        const sliderControl = screen.getByTestId('control');

        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        // pixel:  0   20  40  60  80  100
        // slider: |---|---|---|---|---|
        // values: 0   1   2   3   4   5
        // value:      ��   ��
        // mouse:           ��

        fireEvent.pointerDown(sliderControl, {
          buttons: 1,
          clientX: 41,
        });

        expect(handleValueChange.mock.calls.length).toBe(1);
        expect(handleValueChange.mock.calls[0][0]).not.toBe(value);
        expect(handleValueChange.mock.calls[0][0]).toEqual(value.slice().sort((a, b) => a - b));
      });
    });

    it('should pass "name" and "value" as part of the event.target for onValueChange', async () => {
      const handleValueChange = vi
        .fn()
        .mockImplementation((newValue, data) => (data as any).event.target);

      await render(
        <TestSlider onValueChange={handleValueChange} name="change-testing" value={3} />,
      );

      const slider = screen.getByRole('slider');

      await act(async () => {
        slider.focus();
      });
      fireEvent.change(slider, {
        target: {
          value: 4,
        },
      });

      expect(handleValueChange.mock.calls.length).toBe(1);
      const target = handleValueChange.mock.results[0]?.value;
      expect(target).toEqual({
        name: 'change-testing',
        value: 4,
      });
    });

    it.skipIf(!isJSDOM)(
      'should not rely on the global event when cloning change events',
      async () => {
        const hadGlobalEvent = Object.prototype.hasOwnProperty.call(globalThis, 'event');
        const previousDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'event');
        const globalEventConstructor = class {
          constructor() {
            throw new Error('Should not construct global event');
          }
        };
        const fakeGlobalEvent = {
          type: 'click',
          constructor: globalEventConstructor,
        };

        Object.defineProperty(globalThis, 'event', {
          configurable: true,
          get() {
            return fakeGlobalEvent;
          },
          set() {
            // Ignore assignments from the event system to ensure we never use it.
          },
        });

        try {
          const handleValueChange = vi.fn();

          await render(
            <TestSlider onValueChange={handleValueChange} name="change-testing" value={3} />,
          );

          const slider = screen.getByRole('slider');

          await act(async () => {
            slider.focus();
          });

          expectVitest(() => {
            fireEvent.change(slider, {
              target: {
                value: 4,
              },
            });
          }).not.toThrow();

          expectVitest(handleValueChange).toHaveBeenCalledTimes(1);
        } finally {
          if (hadGlobalEvent && previousDescriptor) {
            Object.defineProperty(globalThis, 'event', previousDescriptor);
          } else {
            delete (globalThis as any).event;
          }
        }
      },
    );

    it.skipIf(isJSDOM)('should handle keyboard changes inside a shadow root', async () => {
      const host = document.createElement('div');
      document.body.appendChild(host);
      const shadowRoot = host.attachShadow({ mode: 'open' });
      const container = document.createElement('div');
      shadowRoot.appendChild(container);

      try {
        const handleValueChange = vi.fn();

        await render(<TestSlider onValueChange={handleValueChange} name="shadow" value={3} />, {
          container,
        });

        const slider = shadowRoot.querySelector('input[type="range"]');
        expectVitest(slider).toBeTruthy();

        if (!slider) {
          return;
        }

        await act(async () => {
          (slider as HTMLInputElement).focus();
        });

        await act(async () => {
          slider.dispatchEvent(new KeyboardEvent('keydown', { key: ARROW_RIGHT, bubbles: true }));
        });

        expectVitest(handleValueChange).toHaveBeenCalledTimes(1);
      } finally {
        await act(async () => {
          host.remove();
        });
      }
    });

    it.skipIf(isJSDOM)(
      'onValueCommitted is called with the same value as the latest onValueChange when pointerUp occurs at a different location than onValueChange',
      async () => {
        const handleValueChange = vi.fn();
        const handleValueCommitted = vi.fn();

        await render(
          <TestSlider
            onValueChange={handleValueChange}
            onValueCommitted={handleValueCommitted}
            defaultValue={0}
          />,
        );

        const sliderControl = screen.getByTestId('control');

        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        fireEvent.pointerDown(sliderControl, {
          buttons: 1,
          clientX: 10,
        });
        fireEvent.pointerMove(sliderControl, {
          buttons: 1,
          clientX: 15,
        });
        fireEvent.pointerUp(sliderControl, {
          buttons: 1,
          clientX: 20,
        });

        expect(handleValueChange.mock.calls.length).toBe(2);
        expect(handleValueChange.mock.calls[0][0]).toBe(10);
        expect(handleValueChange.mock.calls[1][0]).toBe(15);
        expect(handleValueCommitted.mock.calls.length).toBe(1);
        expect(handleValueCommitted.mock.calls[0][0]).toBe(15);
        expect(handleValueCommitted.mock.calls[0][1].reason).toBe('drag');
      },
    );
  });

  describe('keyboard interactions', () => {
    [
      ['ltr', 'horizontal', [ARROW_LEFT, ARROW_DOWN], [ARROW_RIGHT, ARROW_UP]],
      ['ltr', 'vertical', [ARROW_LEFT, ARROW_DOWN], [ARROW_RIGHT, ARROW_UP]],
      ['rtl', 'horizontal', [ARROW_RIGHT, ARROW_DOWN], [ARROW_LEFT, ARROW_UP]],
      ['rtl', 'vertical', [ARROW_RIGHT, ARROW_DOWN], [ARROW_LEFT, ARROW_UP]],
    ].forEach((entry) => {
      const [direction, orientation, decrementKeys, incrementKeys] = entry as [
        direction: TextDirection,
        orientation: Orientation,
        decrementKeys: string[],
        incrementKeys: string[],
      ];

      describe(String(direction), () => {
        describe(`orientation: ${orientation}`, () => {
          decrementKeys.forEach((key) => {
            it(`key: ${key} decrements the value`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`[${key}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(19);
              expect(input).toHaveAttribute('aria-valuenow', '19');
            });

            it(`key: ${key} decrements the value by largeStep when Shift is pressed`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={10}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`{Shift>}{${key}}`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(10);
              expect(input).toHaveAttribute('aria-valuenow', '10');
            });

            it(`key: ${key} stops at min when decrementing while Shift is pressed`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={10}
                      min={15}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`{Shift>}{${key}}`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(15);
              expect(input).toHaveAttribute('aria-valuenow', '15');
            });
          });

          incrementKeys.forEach((key) => {
            it(`key: ${key} increments the value`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`[${key}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(21);
              expect(input).toHaveAttribute('aria-valuenow', '21');
            });

            it(`key: ${key} rounds fractional values to the configured step`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={0.2}
                      min={0}
                      max={1}
                      step={0.1}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`[${key}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(0.3);
              expect(input).toHaveAttribute('aria-valuenow', '0.3');
            });

            it(`key: ${key} increments the value by largeStep when Shift is pressed`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={10}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`{Shift>}{${key}}`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(30);
              expect(input).toHaveAttribute('aria-valuenow', '30');
            });

            it(`key: ${key} stops at max when incrementing while Shift is pressed`, async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={10}
                      max={21}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`{Shift>}{${key}}`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(21);
              expect(input).toHaveAttribute('aria-valuenow', '21');
            });
          });

          describe('key: End', () => {
            it('sets value to max in a single value slider', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      max={77}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`[${END}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(77);
              expect(input).toHaveAttribute('aria-valuenow', '77');
            });

            it('sets value to the maximum possible value in a range slider', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root defaultValue={[20, 50]} max={77} onValueChange={handleValueChange}>
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb index={0} />
                          <Slider.Thumb index={1} />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const [input1, input2] = screen.getAllByRole('slider');

              await user.keyboard('[Tab]');
              expect(input1).toHaveFocus();

              await user.keyboard(`[${END}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual([50, 50]);
              await user.keyboard(`[${END}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);

              await user.keyboard('[Tab]');
              expect(input2).toHaveFocus();

              await user.keyboard(`[${END}]`);
              expect(handleValueChange.mock.calls.length).toBe(2);
              expect(handleValueChange.mock.calls[1][0]).toEqual([50, 77]);
            });
          });

          describe('key: Home', () => {
            it('sets value to min in a single value slider', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      min={17}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard(`[${HOME}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(17);
              expect(input).toHaveAttribute('aria-valuenow', '17');
            });

            it('sets value to the minimum possible value in a range slider', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root defaultValue={[20, 50]} min={7} onValueChange={handleValueChange}>
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb index={0} />
                          <Slider.Thumb index={1} />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const [input1, input2] = screen.getAllByRole('slider');

              await user.keyboard('[Tab]');
              await user.keyboard('[Tab]');
              expect(input2).toHaveFocus();

              await user.keyboard(`[${HOME}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual([20, 20]);
              await user.keyboard(`[${HOME}]`);
              expect(handleValueChange.mock.calls.length).toBe(1);

              await user.keyboard('{Shift>}{Tab}');
              expect(input1).toHaveFocus();

              await user.keyboard(`[${HOME}]`);
              expect(handleValueChange.mock.calls.length).toBe(2);
              expect(handleValueChange.mock.calls[1][0]).toEqual([7, 20]);
            });
          });

          describe('key: PageUp', () => {
            it('increments the value by largeStep', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={5}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard('[PageUp]');
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(25);
              expect(input).toHaveAttribute('aria-valuenow', '25');
            });

            it('preserves largeStep increments when step uses a different grid', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      step={2}
                      largeStep={5}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard('[PageUp]');
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(25);
              expect(input).toHaveAttribute('aria-valuenow', '25');
            });

            it('does not exceed max', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={5}
                      max={21}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard('[PageUp]');
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(21);
              expect(input).toHaveAttribute('aria-valuenow', '21');
            });
          });

          describe('key: PageDown', () => {
            it('decrements the value by largeStep', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={5}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard('[PageDown]');
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(15);
              expect(input).toHaveAttribute('aria-valuenow', '15');
            });

            it('does not go below min', async () => {
              const handleValueChange = vi.fn();
              const { user } = await render(
                <div dir={direction}>
                  <DirectionProvider direction={direction}>
                    <Slider.Root
                      orientation={orientation}
                      defaultValue={20}
                      largeStep={5}
                      min={17}
                      onValueChange={handleValueChange}
                    >
                      <Slider.Control>
                        <Slider.Track>
                          <Slider.Indicator />
                          <Slider.Thumb data-testid="thumb" />
                        </Slider.Track>
                      </Slider.Control>
                    </Slider.Root>
                  </DirectionProvider>
                </div>,
              );

              const input = screen.getByRole('slider');

              await user.keyboard('[Tab]');
              expect(input).toHaveFocus();

              await user.keyboard('[PageDown]');
              expect(handleValueChange.mock.calls.length).toBe(1);
              expect(handleValueChange.mock.calls[0][0]).toEqual(17);
              expect(input).toHaveAttribute('aria-valuenow', '17');
            });
          });
        });
      });

      it('keypresses should correct invalid values', async () => {
        function App() {
          const [val, setVal] = React.useState(5.4698);
          return (
            <Slider.Root value={val} onValueChange={setVal} min={0} max={10} step={1}>
              <Slider.Control>
                <Slider.Track>
                  <Slider.Indicator />
                  <Slider.Thumb data-testid="thumb" />
                </Slider.Track>
              </Slider.Control>
            </Slider.Root>
          );
        }
        const { user } = await render(<App />);

        const input = screen.getByRole('slider');

        expect(input).toHaveAttribute('aria-valuenow', '5.4698');
        await user.keyboard('[Tab]');
        expect(input).toHaveFocus();
        await user.keyboard(`[${ARROW_RIGHT}]`);
        expect(input).toHaveAttribute('aria-valuenow', '6');
      });
    });
  });

  describe('prop: format', () => {
    it('formats the value', async () => {
      function formatValue(v: number) {
        return new Intl.NumberFormat(undefined, USD_NUMBER_FORMAT).format(v);
      }

      await render(<TestSlider defaultValue={50} format={USD_NUMBER_FORMAT} />);

      const value = screen.getByTestId('value');
      const slider = screen.getByRole('slider');
      expect(value).toHaveTextContent(formatValue(50));
      expect(slider).toHaveAttribute('aria-valuetext', formatValue(50));
    });

    it('formats range values', async () => {
      function formatValue(v: number) {
        return new Intl.NumberFormat(undefined, USD_NUMBER_FORMAT).format(v);
      }

      await render(<TestRangeSlider defaultValue={[50, 75]} format={USD_NUMBER_FORMAT} />);

      const value = screen.getByTestId('value');
      expect(value).toHaveTextContent(`${formatValue(50)} – ${formatValue(75)}`);
      const [slider1, slider2] = screen.getAllByRole('slider');
      expect(slider1).toHaveAttribute('aria-valuetext', `${formatValue(50)} start range`);
      expect(slider2).toHaveAttribute('aria-valuetext', `${formatValue(75)} end range`);
    });
  });

  describe('prop: locale', () => {
    it('sets the locale when formatting a single value', async () => {
      const format: Intl.NumberFormatOptions = {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      };
      const expectedValue = new Intl.NumberFormat('de-DE', format).format(70.51);

      await render(<TestSlider value={70.51} format={format} step={0.01} locale="de-DE" />);

      expect(screen.getByTestId('value')).toHaveTextContent(expectedValue);
    });

    it('sets the locale when formatting a range value', async () => {
      const format: Intl.NumberFormatOptions = {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      };
      const expectedValue = `${new Intl.NumberFormat('de-DE', format).format(24.8)} – ${new Intl.NumberFormat('de-DE', format).format(70.51)}`;

      await render(
        <TestRangeSlider value={[24.8, 70.51]} format={format} step={0.01} locale="de-DE" />,
      );

      expect(screen.getByTestId('value')).toHaveTextContent(expectedValue);
    });
  });

  describe('Form', () => {
    it('clears external errors on change', async () => {
      const { user } = await render(
        <Form
          errors={{
            test: 'test',
          }}
        >
          <Field.Root name="test" data-testid="field">
            <TestSlider data-testid="slider" defaultValue={50} />
            <Field.Error data-testid="error" />
          </Field.Root>
        </Form>,
      );

      const slider = screen.getByRole('slider');

      expect(slider).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByTestId('error')).toHaveTextContent('test');

      await user.keyboard('[Tab]');
      expect(slider).toHaveFocus();

      await user.keyboard(`{Shift>}{ArrowRight}`);

      expect(slider).not.toHaveAttribute('aria-invalid');
      expect(screen.queryByTestId('error')).toBe(null);
    });

    describe.skipIf(isJSDOM)('form submission', () => {
      it('should include the slider value', async () => {
        await render(
          <Form
            onSubmit={(event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              expect(formData.get('slider')).toBe('25');
            }}
          >
            <Field.Root name="slider">
              <Slider.Root defaultValue={25} format={USD_NUMBER_FORMAT}>
                <Slider.Control>
                  <Slider.Thumb />
                </Slider.Control>
              </Slider.Root>
            </Field.Root>
            <button type="submit">Submit</button>
          </Form>,
        );

        const submit = screen.getByRole('button');
        fireEvent.click(submit);
      });

      it('should include range slider value', async () => {
        await render(
          <Form
            onSubmit={(event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              expect(formData.getAll('slider')).toEqual(['25', '50']);
            }}
          >
            <Field.Root name="slider">
              <Slider.Root defaultValue={[25, 50]} format={USD_NUMBER_FORMAT}>
                <Slider.Control>
                  <Slider.Thumb />
                  <Slider.Thumb />
                </Slider.Control>
              </Slider.Root>
            </Field.Root>
            <button type="submit">Submit</button>
          </Form>,
        );

        const submit = screen.getByRole('button');
        fireEvent.click(submit);
      });

      it('submits to an external form when `form` is provided', async () => {
        let submitValue: FormDataEntryValue | null = null;

        await render(
          <React.Fragment>
            <form
              id="external-form"
              onSubmit={(event) => {
                event.preventDefault();
                const formData = new FormData(event.currentTarget);
                submitValue = formData.get('slider');
              }}
            >
              <button type="submit">Submit</button>
            </form>
            <Slider.Root name="slider" form="external-form" defaultValue={25}>
              <Slider.Control>
                <Slider.Thumb />
              </Slider.Control>
            </Slider.Root>
          </React.Fragment>,
        );

        fireEvent.click(screen.getByRole('button'));

        expect(submitValue).toBe('25');
      });
    });
  });

  describe('Field', () => {
    it('should receive disabled prop from Field.Root', async () => {
      await render(
        <Field.Root disabled>
          <Slider.Root data-testid="root">
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>
        </Field.Root>,
      );

      const root = screen.getByTestId('root');
      expect(root).toHaveAttribute('data-disabled', '');
    });

    it('should receive name prop from Field.Root', async () => {
      await render(
        <Field.Root name="field-slider">
          <Slider.Root>
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>
        </Field.Root>,
      );

      expect(screen.getByRole('slider')).toHaveAttribute('name', 'field-slider');
    });

    it('[data-touched]', async () => {
      await render(
        <Field.Root>
          <Slider.Root data-testid="root">
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>
        </Field.Root>,
      );

      const root = screen.getByTestId('root');
      const input = screen.getByRole('slider');

      fireEvent.focus(input);
      fireEvent.blur(input);

      expect(root).toHaveAttribute('data-touched', '');
    });

    it('[data-dirty]', async () => {
      await render(
        <Field.Root>
          <Slider.Root data-testid="root">
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>
        </Field.Root>,
      );

      const root = screen.getByTestId('root');
      const input = screen.getByRole('slider');

      expect(root).not.toHaveAttribute('data-dirty');

      fireEvent.change(input, { target: { value: 'value' } });

      expect(root).toHaveAttribute('data-dirty', '');
    });

    it('[data-focused]', async () => {
      await render(
        <Field.Root>
          <Slider.Root data-testid="root">
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>
        </Field.Root>,
      );

      const root = screen.getByTestId('root');
      const input = screen.getByRole('slider');

      expect(root).not.toHaveAttribute('data-focused');

      fireEvent.focus(input);

      expect(root).toHaveAttribute('data-focused', '');

      fireEvent.blur(input);

      expect(root).not.toHaveAttribute('data-focused');
    });

    describe('prop: validate', () => {
      it('validationMode=onSubmit', async () => {
        await render(
          <Form>
            <Field.Root validate={(val) => ((val as number) > 90 ? 'error' : null)}>
              <Slider.Root defaultValue={99} data-testid="root">
                <Slider.Control>
                  <Slider.Thumb data-testid="thumb" />
                </Slider.Control>
              </Slider.Root>
              <Field.Error data-testid="error" />
            </Field.Root>
            <button type="submit">submit</button>
          </Form>,
        );

        const root = screen.getByTestId('root');
        const thumb = screen.getByTestId('thumb');
        const input = screen.getByRole('slider');
        expect(input).not.toHaveAttribute('aria-invalid');
        expect(screen.queryByTestId('error')).toBe(null);

        fireEvent.change(input, { target: { value: '98' } });
        expect(input).not.toHaveAttribute('aria-invalid');
        expect(screen.queryByTestId('error')).toBe(null);

        fireEvent.click(screen.getByText('submit'));
        expect(input).toHaveAttribute('aria-invalid', 'true');
        expect(screen.queryByTestId('error')).not.toBe(null);
        expect(root).toHaveAttribute('data-invalid');
        expect(thumb).toHaveAttribute('data-invalid');

        fireEvent.change(input, { target: { value: '10' } });
        expect(input).not.toHaveAttribute('aria-invalid');
        expect(screen.queryByTestId('error')).toBe(null);
        expect(root).not.toHaveAttribute('data-invalid');
        expect(input).not.toHaveAttribute('data-invalid');
        expect(root).toHaveAttribute('data-valid');
        expect(thumb).toHaveAttribute('data-valid');

        fireEvent.change(input, { target: { value: '94' } });
        expect(input).toHaveAttribute('aria-invalid', 'true');
        expect(screen.queryByTestId('error')).not.toBe(null);

        fireEvent.change(input, { target: { value: '12' } });
        expect(input).not.toHaveAttribute('aria-invalid');
        expect(screen.queryByTestId('error')).toBe(null);
      });

      it('validationMode=onBlur', async () => {
        await render(
          <Field.Root
            validationMode="onBlur"
            validate={(value) => ((value as number) > 1 ? 'error' : null)}
          >
            <Slider.Root>
              <Slider.Control>
                <Slider.Thumb />
              </Slider.Control>
            </Slider.Root>
            <Field.Error data-testid="error" />
          </Field.Root>,
        );

        const input = screen.getByRole('slider');
        expect(input).not.toHaveAttribute('aria-invalid');

        fireEvent.change(input, { target: { value: '2' } });
        expect(input).not.toHaveAttribute('aria-invalid');
        fireEvent.blur(input);
        await flushMicrotasks();
        expect(input).toHaveAttribute('aria-invalid', 'true');
      });

      it('validationMode=onChange', async () => {
        await render(
          <Field.Root
            validationMode="onChange"
            validate={(value) => (Number(value) === 1 ? 'error' : null)}
          >
            <Slider.Root defaultValue={0}>
              <Slider.Control>
                <Slider.Thumb />
              </Slider.Control>
            </Slider.Root>
          </Field.Root>,
        );

        const input = screen.getByRole('slider');
        expect(input).not.toHaveAttribute('aria-invalid');

        fireEvent.change(input, { target: { value: '1' } });
        await flushMicrotasks();
        expect(input).toHaveAttribute('aria-invalid', 'true');
      });

      it('revalidates when the controlled value changes externally', async () => {
        const validateSpy = vi.fn((value: unknown) => (Number(value) === 5 ? 'error' : null));

        function App() {
          const [value, setValue] = React.useState(0);

          return (
            <React.Fragment>
              <Field.Root validationMode="onChange" validate={validateSpy} name="volume">
                <Slider.Root value={value} onValueChange={(next) => setValue(next as number)}>
                  <Slider.Control>
                    <Slider.Thumb />
                  </Slider.Control>
                </Slider.Root>
              </Field.Root>
              <button type="button" onClick={() => setValue(5)}>
                Set externally
              </button>
            </React.Fragment>
          );
        }

        await render(<App />);

        const slider = screen.getByRole('slider');
        const toggle = screen.getByText('Set externally');

        expect(slider).not.toHaveAttribute('aria-invalid');
        const initialCallCount = validateSpy.mock.calls.length;

        fireEvent.click(toggle);
        await flushMicrotasks();

        expect(validateSpy.mock.calls.length).toBe(initialCallCount + 1);
        expect(validateSpy.mock.lastCall?.[0]).toBe(5);
        expect(slider).toHaveAttribute('aria-invalid', 'true');
      });

      it('receives an array value for range sliders', async () => {
        const validateSpy = vi.fn();
        await render(
          <Form>
            <Field.Root validate={validateSpy}>
              <Slider.Root defaultValue={[5, 12]}>
                <Slider.Control>
                  <Slider.Thumb index={0} />
                  <Slider.Thumb index={1} />
                </Slider.Control>
              </Slider.Root>
              <Field.Error data-testid="error" />
            </Field.Root>
            <button type="submit">submit</button>
          </Form>,
        );

        fireEvent.click(screen.getByText('submit'));
        expect(validateSpy.mock.calls.length).toBe(1);
        expect(validateSpy.mock.calls[0][0]).toEqual([5, 12]);
      });

      it('does not call validate on change when validationMode is omitted', async () => {
        const validateSpy = vi.fn();
        await render(
          <Form>
            <Field.Root validate={validateSpy}>
              <Slider.Root defaultValue={50}>
                <Slider.Control data-testid="control">
                  <Slider.Track>
                    <Slider.Thumb aria-label="Value" />
                  </Slider.Track>
                </Slider.Control>
              </Slider.Root>
            </Field.Root>
            <button type="submit">submit</button>
          </Form>,
        );

        expect(validateSpy.mock.calls.length).toBe(0);

        const sliderControl = screen.getByTestId('control');
        fireEvent.pointerDown(sliderControl, { buttons: 1, clientX: 10 });
        fireEvent.pointerUp(sliderControl, { buttons: 1, clientX: 30 });

        expect(validateSpy.mock.calls.length).toBe(0);
      });
    });

    it('Field.Label', async () => {
      await render(
        <Field.Root>
          <Slider.Root>
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>
          <Field.Label data-testid="label" />
        </Field.Root>,
      );

      expect(screen.getByRole('slider')).toHaveAttribute(
        'aria-labelledby',
        screen.getByTestId('label').id,
      );
    });

    it('Slider.Label', async () => {
      await render(
        <Slider.Root>
          <Slider.Label data-testid="label" />
          <Slider.Control>
            <Slider.Thumb />
          </Slider.Control>
        </Slider.Root>,
      );

      expect(screen.getByRole('slider')).toHaveAttribute(
        'aria-labelledby',
        screen.getByTestId('label').id,
      );
    });

    it('Slider.Label focuses slider on click', async () => {
      const { user } = await render(
        <Slider.Root>
          <Slider.Label data-testid="label">Volume</Slider.Label>
          <Slider.Control>
            <Slider.Thumb />
          </Slider.Control>
        </Slider.Root>,
      );

      await user.click(screen.getByTestId('label'));

      expect(screen.getByRole('slider')).toHaveFocus();
    });

    it('Slider.Label does not focus a thumb on click for range sliders', async () => {
      const { user } = await render(
        <Slider.Root defaultValue={[20, 80]}>
          <Slider.Label data-testid="label">Price range</Slider.Label>
          <Slider.Control>
            <Slider.Track>
              <Slider.Thumb aria-label="Minimum price" />
              <Slider.Thumb aria-label="Maximum price" />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      await user.click(screen.getByTestId('label'));

      const [minimumSlider, maximumSlider] = screen.getAllByRole('slider');
      expect(minimumSlider).not.toHaveFocus();
      expect(maximumSlider).not.toHaveFocus();
    });

    it('does not set aria-labelledby when getAriaLabel is provided', async () => {
      await render(
        <Slider.Root defaultValue={[20, 80]}>
          <Slider.Label>Price range</Slider.Label>
          <Slider.Control>
            <Slider.Track>
              <Slider.Thumb getAriaLabel={() => 'Minimum price'} />
              <Slider.Thumb getAriaLabel={() => 'Maximum price'} />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      const [minimumSlider, maximumSlider] = screen.getAllByRole('slider');
      expect(minimumSlider).toHaveAttribute('aria-label', 'Minimum price');
      expect(maximumSlider).toHaveAttribute('aria-label', 'Maximum price');
      expect(minimumSlider).not.toHaveAttribute('aria-labelledby');
      expect(maximumSlider).not.toHaveAttribute('aria-labelledby');
    });

    it('does not set fallback aria-labelledby when no label is rendered', async () => {
      await render(
        <Slider.Root>
          <Slider.Control>
            <Slider.Thumb aria-label="Volume" />
          </Slider.Control>
        </Slider.Root>,
      );

      await waitFor(() => {
        expect(screen.getByRole('slider')).not.toHaveAttribute('aria-labelledby');
      });
    });

    it('updates Slider.Label linkage when root id changes', async () => {
      const { setProps } = await render(
        <Slider.Root id="first" defaultValue={30} data-testid="root">
          <Slider.Label data-testid="label">Volume</Slider.Label>
          <Slider.Control>
            <Slider.Track>
              <Slider.Thumb />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      await setProps({ id: 'second' });

      /* eslint-disable testing-library/no-wait-for-multiple-assertions */
      await waitFor(() => {
        const root = screen.getByTestId('root');
        const label = screen.getByTestId('label');
        const slider = screen.getByRole('slider');
        expect(root).toHaveAttribute('id', 'second');
        expect(label.id).toBe('second-label');
        expect(root).toHaveAttribute('aria-labelledby', label.id);
        expect(slider).toHaveAttribute('aria-labelledby', label.id);
      });
      /* eslint-enable testing-library/no-wait-for-multiple-assertions */
    });

    it('Field.Description', async () => {
      await render(
        <Field.Root>
          <Slider.Root data-testid="slider">
            <Slider.Control />
          </Slider.Root>
          <Field.Description data-testid="description" />
        </Field.Root>,
      );

      expect(screen.getByTestId('slider')).toHaveAttribute(
        'aria-describedby',
        screen.getByTestId('description').id,
      );
    });
  });
});

// ---- packages/react/src/slider/thumb/SliderThumb.test.tsx ----
import { expect, vi } from 'vitest';
import * as React from 'react';
import { fireEvent, screen, waitFor } from '@mui/internal-test-utils';
import { Slider } from '@base-ui/react/slider';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';
import { isWebKit } from '@base-ui/utils/detectBrowser';
import { createTouches, getHorizontalSliderRect } from '../utils/test-utils';

describe('<Slider.Thumb />', () => {
  const { render, renderToString } = createRenderer();

  describeConformance(<Slider.Thumb />, () => ({
    render: (node) => {
      return render(<Slider.Root>{node}</Slider.Root>);
    },
    refInstanceof: window.HTMLDivElement,
  }));

  describe('ARIA attributes', () => {
    ['aria-label', 'aria-labelledby', 'aria-describedby'].forEach((attr) => {
      it(`forwards ${attr} to the input`, async () => {
        await render(
          <Slider.Root defaultValue={50}>
            <Slider.Control>
              <Slider.Thumb
                {...{
                  [attr]: 'test',
                }}
              />
            </Slider.Control>
          </Slider.Root>,
        );
        expect(screen.getByRole('slider')).toHaveAttribute(attr, 'test');
      });
    });
  });

  // AT (e.g. Android Talkback) may use increase/decrease actions to interact
  // with the slider which works on `input type="range"` via change events, but
  // not pure ARIA implementations using `div role="slider"`. The `input`
  // element(s) must be the only focusable element(s).
  // See:
  // - https://issues.chromium.org/issues/40816094
  // - https://github.com/mui/material-ui/issues/23506
  describe('events', () => {
    describe.skipIf(isJSDOM)('focus and blur', () => {
      it('single thumb', async () => {
        const focusAndBlurSpy = vi.fn((event) => event.target);
        const { user } = await render(
          <Slider.Root defaultValue={50}>
            <Slider.Control>
              <Slider.Thumb onFocus={focusAndBlurSpy} onBlur={focusAndBlurSpy} />
            </Slider.Control>
          </Slider.Root>,
        );
        expect(document.body).toHaveFocus();
        const input = screen.getByRole('slider');
        expect(input.tagName).toBe('INPUT');
        expect(input).toHaveAttribute('type', 'range');

        await user.keyboard('[Tab]');
        // We assert above that the tabbable elements of the slider are
        // input[type="range"] because TalkBack doesn't simulate keyboard events for increments
        // or decrements (proof: https://issues.chromium.org/issues/40816094). Instead, it triggers change events on those native slider inputs.
        expect(input).toHaveFocus();
        expect(focusAndBlurSpy.mock.calls.length).toBe(1);
        expect(focusAndBlurSpy.mock.results[0]?.value).toBe(input);

        await user.keyboard('[Tab]');
        expect(document.body).toHaveFocus();
        expect(focusAndBlurSpy.mock.calls.length).toBe(2);
        expect(focusAndBlurSpy.mock.results.at(-1)?.value).toBe(input);
      });

      it('multiple thumbs', async () => {
        const focusSpy = vi.fn((event) => event.target);
        const blurSpy = vi.fn((event) => event.target);
        const { user } = await render(
          <Slider.Root defaultValue={[50, 70]}>
            <Slider.Control>
              <Slider.Thumb onFocus={focusSpy} onBlur={blurSpy} />
              <Slider.Thumb onFocus={focusSpy} onBlur={blurSpy} />
            </Slider.Control>
          </Slider.Root>,
        );
        expect(document.body).toHaveFocus();
        const [slider1, slider2] = screen.getAllByRole('slider');
        expect(slider1).toHaveProperty('tagName', 'INPUT');
        expect(slider1).toHaveAttribute('type', 'range');
        expect(slider2).toHaveProperty('tagName', 'INPUT');
        expect(slider2).toHaveAttribute('type', 'range');

        await user.keyboard('[Tab]');
        expect(slider1).toHaveFocus();
        expect(focusSpy.mock.calls.length).toBe(1);
        expect(focusSpy.mock.results.at(-1)?.value).toBe(slider1);

        await user.keyboard('[Tab]');
        expect(blurSpy.mock.calls.length).toBe(1);
        expect(blurSpy.mock.results.at(-1)?.value).toBe(slider1);
        expect(slider2).toHaveFocus();
        expect(focusSpy.mock.calls.length).toBe(2);
        expect(focusSpy.mock.results.at(-1)?.value).toBe(slider2);

        await user.keyboard('[Tab]');
        expect(blurSpy.mock.calls.length).toBe(2);
        expect(blurSpy.mock.results.at(-1)?.value).toBe(slider2);
        expect(document.body).toHaveFocus();
      });

      it('does not emit extra blur and focus events when restoring focus-visible', async () => {
        const focusSpy = vi.fn((event) => event.target);
        const blurSpy = vi.fn((event) => event.target);

        await render(
          <Slider.Root defaultValue={40}>
            <Slider.Control data-testid="control">
              <Slider.Thumb onFocus={focusSpy} onBlur={blurSpy} />
            </Slider.Control>
          </Slider.Root>,
        );

        const sliderControl = screen.getByTestId('control');
        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(
          getHorizontalSliderRect,
        );

        const slider = screen.getByRole('slider');

        fireEvent.pointerDown(sliderControl, {
          pointerId: 1,
          pointerType: 'mouse',
          button: 0,
          buttons: 1,
          clientX: 40,
          clientY: 0,
        });

        await waitFor(() => {
          expect(slider).toHaveFocus();
        });
        expect(focusSpy).toHaveBeenCalledTimes(1);
        expect(focusSpy.mock.results[0]?.value).toBe(slider);
        expect(blurSpy).not.toHaveBeenCalled();

        fireEvent.keyDown(slider, { key: 'ArrowRight' });

        expect(focusSpy).toHaveBeenCalledTimes(1);
        expect(blurSpy).not.toHaveBeenCalled();
      });
    });

    describe('change', () => {
      it('handles change events', async () => {
        const handleValueChange = vi.fn();
        await render(
          <Slider.Root defaultValue={50} onValueChange={handleValueChange}>
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>,
        );

        const slider = screen.getByRole('slider');
        expect(slider).toHaveAttribute('aria-valuenow', '50');
        fireEvent.change(slider, { target: { value: '51' } });
        expect(handleValueChange.mock.calls.length).toBe(1);
        expect(slider).toHaveAttribute('aria-valuenow', '51');
      });

      it('does not change the value beyond min and max', async () => {
        const handleValueChange = vi.fn();
        await render(
          <Slider.Root defaultValue={50} min={40} max={60} onValueChange={handleValueChange}>
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>,
        );

        const slider = screen.getByRole('slider');
        expect(slider).toHaveAttribute('aria-valuenow', '50');

        fireEvent.change(slider, { target: { value: '30' } });
        expect(slider).toHaveAttribute('aria-valuenow', '40');
        expect(handleValueChange.mock.calls.length).toBe(1);
        fireEvent.change(slider, { target: { value: '30' } });
        expect(handleValueChange.mock.calls.length).toBe(1);

        fireEvent.change(slider, { target: { value: '70' } });
        expect(slider).toHaveAttribute('aria-valuenow', '60');
        expect(handleValueChange.mock.calls.length).toBe(2);
        fireEvent.change(slider, { target: { value: '70' } });
        expect(handleValueChange.mock.calls.length).toBe(2);
      });

      it('handles non-integer values', async () => {
        const handleValueChange = vi.fn();
        await render(
          <Slider.Root
            defaultValue={50}
            min={-100}
            max={100}
            step={0.00000001}
            onValueChange={handleValueChange}
          >
            <Slider.Control>
              <Slider.Thumb />
            </Slider.Control>
          </Slider.Root>,
        );

        const slider = screen.getByRole('slider');
        expect(slider).toHaveAttribute('aria-valuenow', '50');
        expect(slider).toHaveAttribute('step', '1e-8');

        fireEvent.change(slider, { target: { value: '51.1' } });
        expect(slider).toHaveAttribute('aria-valuenow', '51.1');

        fireEvent.change(slider, { target: { value: '0.00000005' } });
        expect(slider).toHaveAttribute('aria-valuenow', '5e-8');

        fireEvent.change(slider, { target: { value: '1e-7' } });
        expect(slider).toHaveAttribute('aria-valuenow', '1e-7');
      });
    });
  });

  describe('prop: tabIndex', () => {
    it('does not apply tabIndex to the thumb element by default', async () => {
      await render(
        <Slider.Root defaultValue={50}>
          <Slider.Control>
            <Slider.Thumb data-testid="thumb" />
          </Slider.Control>
        </Slider.Root>,
      );

      expect(screen.getByTestId('thumb')).not.toHaveAttribute('tabindex');
      expect(screen.getByRole('slider')).toHaveProperty('tabIndex', 0);
    });

    it('can be removed from the tab sequence', async () => {
      const { user } = await render(
        <Slider.Root defaultValue={50}>
          <Slider.Control>
            <Slider.Thumb tabIndex={-1} />
          </Slider.Control>
        </Slider.Root>,
      );

      expect(screen.getByRole('slider')).toHaveProperty('tabIndex', -1);
      expect(document.body).toHaveFocus();
      await user.keyboard('[Tab]');
      expect(document.body).toHaveFocus();
    });
  });

  describe('prop: children', () => {
    it('renders the nested input as a sibling to children', async () => {
      await render(
        <Slider.Root defaultValue={50}>
          <Slider.Control>
            <Slider.Thumb data-testid="thumb">
              <span data-testid="child" />
            </Slider.Thumb>
          </Slider.Control>
        </Slider.Root>,
      );

      const thumb = screen.getByTestId('thumb');
      expect(thumb.querySelector('input[type="range"]')).toBe(screen.getByRole('slider'));
      expect(thumb.querySelector('[data-testid="child"]')).toBe(screen.getByTestId('child'));
    });

    it('renders the nested input when using the short form render prop', async () => {
      await render(
        <Slider.Root defaultValue={50}>
          <Slider.Control>
            <Slider.Thumb render={<div data-testid="thumb" />}>
              <span data-testid="child" />
            </Slider.Thumb>
          </Slider.Control>
        </Slider.Root>,
      );

      const thumb = screen.getByTestId('thumb');
      expect(thumb.querySelector('input[type="range"]')).toBe(screen.getByRole('slider'));
      expect(thumb.querySelector('[data-testid="child"]')).toBe(screen.getByTestId('child'));
    });

    it('renders the nested input when using the long form render prop', async () => {
      await render(
        <Slider.Root defaultValue={50}>
          <Slider.Control>
            <Slider.Thumb render={(props) => <div data-testid="thumb" {...props} />}>
              <span data-testid="child" />
            </Slider.Thumb>
          </Slider.Control>
        </Slider.Root>,
      );

      const thumb = screen.getByTestId('thumb');
      expect(thumb.querySelector('input[type="range"]')).toBe(screen.getByRole('slider'));
      expect(thumb.querySelector('[data-testid="child"]')).toBe(screen.getByTestId('child'));
    });
  });

  describe('prop: inputRef', () => {
    it('can focus the input element', async () => {
      function App() {
        const inputRef = React.useRef<HTMLInputElement>(null);
        return (
          <React.Fragment>
            <Slider.Root defaultValue={50}>
              <Slider.Control>
                <Slider.Thumb inputRef={inputRef} />
              </Slider.Control>
            </Slider.Root>
            <button
              onClick={() => {
                if (inputRef.current) {
                  inputRef.current.focus();
                }
              }}
            >
              Button
            </button>
          </React.Fragment>
        );
      }
      const { user } = await render(<App />);

      expect(document.body).toHaveFocus();
      await user.click(screen.getByText('Button'));
      expect(screen.getByRole('slider')).toHaveFocus();
    });
  });

  describe('stacking order', () => {
    it('relies on DOM order before any thumb is used', async () => {
      await render(
        <Slider.Root defaultValue={[20, 20]}>
          <Slider.Control>
            <Slider.Thumb data-testid="thumb-0" />
            <Slider.Thumb data-testid="thumb-1" />
          </Slider.Control>
        </Slider.Root>,
      );

      expect(screen.getByTestId('thumb-0').style.zIndex).toBe('');
      expect(screen.getByTestId('thumb-1').style.zIndex).toBe('');
    });

    it('keeps the most recently active thumb on top after focus moves away', async () => {
      const { user } = await render(
        <Slider.Root defaultValue={[20, 20]}>
          <Slider.Control>
            <Slider.Thumb data-testid="thumb-0" />
            <Slider.Thumb data-testid="thumb-1" />
          </Slider.Control>
        </Slider.Root>,
      );

      const [thumb0, thumb1] = [screen.getByTestId('thumb-0'), screen.getByTestId('thumb-1')];

      await user.keyboard('[Tab]');
      expect(screen.getAllByRole('slider')[0]).toHaveFocus();
      expect(thumb0.style.zIndex).toBe('2');

      await user.keyboard('[Tab]');
      expect(screen.getAllByRole('slider')[1]).toHaveFocus();
      expect(thumb1.style.zIndex).toBe('2');

      await user.keyboard('[Tab]');
      expect(document.body).toHaveFocus();
      expect(thumb1.style.zIndex).toBe('1');
      expect(thumb0.style.zIndex).toBe('');
    });
  });

  describe('prop: thumbAlignment', () => {
    it.skipIf(isJSDOM)('recomputes inset positions when the slider becomes visible', async () => {
      function App() {
        const [visible, setVisible] = React.useState(false);

        return (
          <React.Fragment>
            <button type="button" onClick={() => setVisible(true)}>
              show
            </button>
            <div style={{ display: visible ? 'block' : 'none' }}>
              <Slider.Root defaultValue={30} thumbAlignment="edge" style={{ width: '100px' }}>
                <Slider.Control
                  data-testid="control"
                  style={{ position: 'relative', width: '100%', height: '10px' }}
                >
                  <Slider.Track style={{ position: 'relative', width: '100%', height: '10px' }}>
                    <Slider.Indicator data-testid="indicator" />
                    <Slider.Thumb data-testid="thumb" style={{ width: '10px', height: '10px' }} />
                  </Slider.Track>
                </Slider.Control>
              </Slider.Root>
            </div>
          </React.Fragment>
        );
      }

      const { user } = await render(<App />);

      const thumb = screen.getByTestId('thumb');
      const indicator = screen.getByTestId('indicator');

      await waitFor(() => {
        expect(thumb.style.visibility).toBe('hidden');
        expect(thumb.style.getPropertyValue('--position')).toBe('0%');
        expect(indicator.style.visibility).toBe('hidden');
        expect(indicator.style.getPropertyValue('--start-position')).toBe('0%');
      });

      await user.click(screen.getByRole('button', { name: 'show' }));

      await waitFor(() => {
        expect(thumb.style.visibility).toBe('');
        expect(thumb.style.getPropertyValue('--position')).toBe('32%');
        expect(indicator.style.visibility).toBe('');
        expect(indicator.style.getPropertyValue('--start-position')).toBe('32%');
      });
    });

    it.skipIf(isJSDOM)(
      'recomputes range inset positions when the slider becomes visible',
      async () => {
        function App() {
          const [visible, setVisible] = React.useState(false);

          return (
            <React.Fragment>
              <button type="button" onClick={() => setVisible(true)}>
                show
              </button>
              <div style={{ display: visible ? 'block' : 'none' }}>
                <Slider.Root
                  defaultValue={[30, 70]}
                  thumbAlignment="edge"
                  style={{ width: '100px' }}
                >
                  <Slider.Control
                    data-testid="control"
                    style={{ position: 'relative', width: '100%', height: '10px' }}
                  >
                    <Slider.Track style={{ position: 'relative', width: '100%', height: '10px' }}>
                      <Slider.Indicator data-testid="indicator" />
                      <Slider.Thumb
                        data-testid="start-thumb"
                        style={{ width: '10px', height: '10px' }}
                      />
                      <Slider.Thumb
                        data-testid="end-thumb"
                        style={{ width: '10px', height: '10px' }}
                      />
                    </Slider.Track>
                  </Slider.Control>
                </Slider.Root>
              </div>
            </React.Fragment>
          );
        }

        const { user } = await render(<App />);

        const startThumb = screen.getByTestId('start-thumb');
        const endThumb = screen.getByTestId('end-thumb');
        const indicator = screen.getByTestId('indicator');

        await waitFor(() => {
          expect(startThumb.style.visibility).toBe('hidden');
          expect(startThumb.style.getPropertyValue('--position')).toBe('0%');
          expect(endThumb.style.visibility).toBe('hidden');
          expect(endThumb.style.getPropertyValue('--position')).toBe('0%');
          expect(indicator.style.visibility).toBe('hidden');
          expect(indicator.style.getPropertyValue('--start-position')).toBe('0%');
          expect(indicator.style.getPropertyValue('--relative-size')).toBe('0%');
        });

        await user.click(screen.getByRole('button', { name: 'show' }));

        await waitFor(() => {
          expect(startThumb.style.visibility).toBe('');
          expect(startThumb.style.getPropertyValue('--position')).toBe('32%');
          expect(endThumb.style.visibility).toBe('');
          expect(endThumb.style.getPropertyValue('--position')).toBe('68%');
          expect(indicator.style.visibility).toBe('');
          expect(indicator.style.getPropertyValue('--start-position')).toBe('32%');
          expect(indicator.style.getPropertyValue('--relative-size')).toBe('36%');
        });
      },
    );
  });

  /**
   * Browser tests render with 1024px width by default, so most tests here set
   * the component to `width: 100px` to make the asserted values more readable.
   */
  describe.skipIf(isJSDOM || isWebKit || typeof Touch === 'undefined')('positioning styles', () => {
    describe('positions the thumb when dragged', () => {
      it('single thumb', async () => {
        await render(
          <Slider.Root
            style={{
              width: '1000px',
            }}
          >
            <Slider.Control data-testid="control">
              <Slider.Track>
                <Slider.Indicator />
                <Slider.Thumb data-testid="thumb" />
              </Slider.Track>
            </Slider.Control>
          </Slider.Root>,
        );

        const sliderControl = screen.getByTestId('control');

        const thumbStyles = getComputedStyle(screen.getByTestId('thumb'));

        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() =>
          getHorizontalSliderRect(1000),
        );

        fireEvent.touchStart(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 20, clientY: 0 }]),
        );
        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 199, clientY: 0 }]),
        );
        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 199, clientY: 0 }]),
        );

        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 199, clientY: 0 }]),
        );

        expect(thumbStyles.getPropertyValue('left')).toBe('200px');
        fireEvent.touchEnd(
          document.body,
          createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]),
        );
        expect(thumbStyles.getPropertyValue('left')).toBe('200px');
      });

      it('multiple thumbs', async () => {
        await render(
          <Slider.Root
            defaultValue={[20, 40]}
            style={{
              width: '1000px',
            }}
          >
            <Slider.Control data-testid="control">
              <Slider.Track>
                <Slider.Indicator />
                <Slider.Thumb data-testid="thumb" />
                <Slider.Thumb data-testid="thumb" />
              </Slider.Track>
            </Slider.Control>
          </Slider.Root>,
        );

        const sliderControl = screen.getByTestId('control');

        const computedStyles = {
          thumb1: getComputedStyle(screen.getAllByTestId('thumb')[0]),
          thumb2: getComputedStyle(screen.getAllByTestId('thumb')[1]),
        };

        vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() =>
          getHorizontalSliderRect(1000),
        );

        fireEvent.touchStart(
          sliderControl,
          createTouches([{ identifier: 1, clientX: 400, clientY: 0 }]),
        );
        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 699, clientY: 0 }]),
        );
        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 699, clientY: 0 }]),
        );

        fireEvent.touchMove(
          document.body,
          createTouches([{ identifier: 1, clientX: 699, clientY: 0 }]),
        );

        expect(computedStyles.thumb2.getPropertyValue('left')).toBe('700px');
        fireEvent.touchEnd(
          document.body,
          createTouches([{ identifier: 1, clientX: 0, clientY: 0 }]),
        );
        expect(computedStyles.thumb1.getPropertyValue('left')).toBe('200px');
        expect(computedStyles.thumb2.getPropertyValue('left')).toBe('700px');
      });

      describe('prop: thumbCollisionBehavior', () => {
        function getSliderValues() {
          return screen
            .getAllByRole('slider')
            .map((input) => Number(input.getAttribute('aria-valuenow')));
        }

        it('prevents thumbs from passing each other when set to "none"', async () => {
          await render(
            <Slider.Root
              defaultValue={[20, 40]}
              thumbCollisionBehavior="none"
              style={{
                width: '1000px',
              }}
            >
              <Slider.Control data-testid="control">
                <Slider.Track>
                  <Slider.Indicator />
                  <Slider.Thumb index={0} data-testid="thumb1" />
                  <Slider.Thumb index={1} />
                </Slider.Track>
              </Slider.Control>
            </Slider.Root>,
          );

          const sliderControl = screen.getByTestId('control');

          vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() =>
            getHorizontalSliderRect(1000),
          );

          fireEvent.touchStart(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
          );
          fireEvent.touchMove(
            document.body,
            createTouches([{ identifier: 1, clientX: 600, clientY: 0 }]),
          );
          fireEvent.touchEnd(
            document.body,
            createTouches([{ identifier: 1, clientX: 600, clientY: 0 }]),
          );

          expect(getSliderValues()).toEqual([40, 40]);
        });

        it('pushes adjacent thumbs forward when set to "push"', async () => {
          await render(
            <Slider.Root
              defaultValue={[20, 40]}
              thumbCollisionBehavior="push"
              style={{
                width: '1000px',
              }}
            >
              <Slider.Control data-testid="control">
                <Slider.Track>
                  <Slider.Indicator />
                  <Slider.Thumb index={0} data-testid="thumb1" />
                  <Slider.Thumb index={1} />
                </Slider.Track>
              </Slider.Control>
            </Slider.Root>,
          );

          const sliderControl = screen.getByTestId('control');

          vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() =>
            getHorizontalSliderRect(1000),
          );

          fireEvent.touchStart(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
          );
          fireEvent.touchMove(
            document.body,
            createTouches([{ identifier: 1, clientX: 650, clientY: 0 }]),
          );
          fireEvent.touchEnd(
            document.body,
            createTouches([{ identifier: 1, clientX: 650, clientY: 0 }]),
          );

          expect(getSliderValues()).toEqual([65, 65]);
        });

        it('allows thumbs to swap when set to "swap"', async () => {
          await render(
            <Slider.Root
              defaultValue={[20, 40]}
              thumbCollisionBehavior="swap"
              style={{
                width: '1000px',
              }}
            >
              <Slider.Control data-testid="control">
                <Slider.Track>
                  <Slider.Indicator />
                  <Slider.Thumb index={0} data-testid="thumb1" />
                  <Slider.Thumb index={1} />
                </Slider.Track>
              </Slider.Control>
            </Slider.Root>,
          );

          const sliderControl = screen.getByTestId('control');

          vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() =>
            getHorizontalSliderRect(1000),
          );

          fireEvent.touchStart(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
          );
          fireEvent.touchMove(
            document.body,
            createTouches([{ identifier: 1, clientX: 700, clientY: 0 }]),
          );
          fireEvent.touchEnd(
            document.body,
            createTouches([{ identifier: 1, clientX: 700, clientY: 0 }]),
          );

          expect(getSliderValues()).toEqual([40, 70]);
        });

        it('maintains minimum steps between values when swapping', async () => {
          await render(
            <Slider.Root
              defaultValue={[20, 40, 60]}
              minStepsBetweenValues={10}
              thumbCollisionBehavior="swap"
              style={{
                width: '1000px',
              }}
            >
              <Slider.Control data-testid="control">
                <Slider.Track>
                  <Slider.Indicator />
                  <Slider.Thumb index={0} data-testid="thumb1" />
                  <Slider.Thumb index={1} />
                  <Slider.Thumb index={2} />
                </Slider.Track>
              </Slider.Control>
            </Slider.Root>,
          );

          const sliderControl = screen.getByTestId('control');

          vi.spyOn(sliderControl, 'getBoundingClientRect').mockImplementation(() =>
            getHorizontalSliderRect(1000),
          );

          fireEvent.touchStart(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 200, clientY: 0 }]),
          );
          fireEvent.touchMove(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 500, clientY: 0 }]),
          );
          fireEvent.touchMove(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 550, clientY: 0 }]),
          );
          fireEvent.touchMove(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 800, clientY: 0 }]),
          );
          fireEvent.touchEnd(
            sliderControl,
            createTouches([{ identifier: 1, clientX: 800, clientY: 0 }]),
          );

          expect(getSliderValues()).toEqual([30, 50, 80]);
        });
      });
    });

    describe('positions the thumb when the controlled value changes externally', () => {
      it('single thumb', async () => {
        function App() {
          const [val, setVal] = React.useState(20);
          return (
            <React.Fragment>
              <button onClick={() => setVal(55)} />
              <Slider.Root
                value={val}
                onValueChange={(newVal) => setVal(newVal as number)}
                style={{
                  width: '100px',
                }}
              >
                <Slider.Control data-testid="control">
                  <Slider.Track>
                    <Slider.Indicator />
                    <Slider.Thumb data-testid="thumb" />
                  </Slider.Track>
                </Slider.Control>
              </Slider.Root>
            </React.Fragment>
          );
        }
        await render(<App />);

        const thumbStyles = getComputedStyle(screen.getByTestId('thumb'));
        expect(thumbStyles.getPropertyValue('left')).toBe('20px');

        fireEvent.click(screen.getByRole('button'));
        expect(thumbStyles.getPropertyValue('left')).toBe('55px');
      });

      it('multiple thumbs', async () => {
        function App() {
          const [val, setVal] = React.useState([20, 50]);
          return (
            <React.Fragment>
              <button onClick={() => setVal([33, 72])} />
              <Slider.Root
                value={val}
                onValueChange={(newVal) => setVal(newVal as number[])}
                style={{
                  width: '100px',
                }}
              >
                <Slider.Control data-testid="control">
                  <Slider.Track>
                    <Slider.Indicator />
                    <Slider.Thumb data-testid="thumb" />
                    <Slider.Thumb data-testid="thumb" />
                  </Slider.Track>
                </Slider.Control>
              </Slider.Root>
            </React.Fragment>
          );
        }
        await render(<App />);

        const computedStyles = {
          thumb1: getComputedStyle(screen.getAllByTestId('thumb')[0]),
          thumb2: getComputedStyle(screen.getAllByTestId('thumb')[1]),
        };

        expect(computedStyles.thumb1.getPropertyValue('left')).toBe('20px');
        expect(computedStyles.thumb2.getPropertyValue('left')).toBe('50px');

        fireEvent.click(screen.getByRole('button'));
        expect(computedStyles.thumb1.getPropertyValue('left')).toBe('33px');
        expect(computedStyles.thumb2.getPropertyValue('left')).toBe('72px');
      });
    });

    it('thumb should not go out of bounds when the controlled value goes out of bounds', async () => {
      function App() {
        const [val, setVal] = React.useState(50);
        return (
          <React.Fragment>
            <button onClick={() => setVal(119.9)}>max</button>
            <button onClick={() => setVal(-7.31)}>min</button>
            <Slider.Root
              value={val}
              onValueChange={setVal}
              min={0}
              max={100}
              style={{ width: '100px' }}
            >
              <Slider.Control data-testid="control">
                <Slider.Track>
                  <Slider.Indicator />
                  <Slider.Thumb data-testid="thumb" />
                </Slider.Track>
              </Slider.Control>
            </Slider.Root>
          </React.Fragment>
        );
      }
      const { user } = await render(<App />);

      const thumbStyles = getComputedStyle(screen.getByTestId('thumb'));
      expect(thumbStyles.getPropertyValue('left')).toBe('50px');

      await user.click(screen.getByRole('button', { name: 'max' }));
      expect(thumbStyles.getPropertyValue('left')).toBe('100px');

      await user.click(screen.getByRole('button', { name: 'min' }));
      expect(thumbStyles.getPropertyValue('left')).toBe('0px');
    });
  });

  describe.skipIf(isJSDOM)('server-side rendering', () => {
    it('single thumb', async () => {
      await renderToString(
        <Slider.Root
          defaultValue={30}
          style={{
            width: '100px',
          }}
        >
          <Slider.Value />
          <Slider.Control>
            <Slider.Track>
              <Slider.Indicator />
              <Slider.Thumb data-testid="thumb" />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      expect(getComputedStyle(screen.getByTestId('thumb')).getPropertyValue('left')).toBe('30px');
    });

    it('renders the inline pre-hydration script for edge-aligned thumbs', async () => {
      await renderToString(
        <Slider.Root
          defaultValue={30}
          thumbAlignment="edge"
          style={{
            width: '100px',
          }}
        >
          <Slider.Value />
          <Slider.Control>
            <Slider.Track>
              <Slider.Indicator />
              <Slider.Thumb data-testid="thumb" />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      expect(document.querySelector('script')).not.toBe(null);
    });

    it('multiple thumbs', async () => {
      renderToString(
        <Slider.Root
          defaultValue={[30, 40]}
          style={{
            width: '100px',
          }}
        >
          <Slider.Value />
          <Slider.Control>
            <Slider.Track>
              <Slider.Thumb index={0} data-testid="thumb" />
              <Slider.Thumb index={1} data-testid="thumb" />
            </Slider.Track>
          </Slider.Control>
        </Slider.Root>,
      );

      const [thumb0, thumb1] = Array.from(await screen.findAllByTestId('thumb'));

      expect(getComputedStyle(thumb0).getPropertyValue('left')).toBe('30px');
      expect(getComputedStyle(thumb1).getPropertyValue('left')).toBe('40px');
    });
  });
});

// ---- packages/react/src/slider/track/SliderTrack.test.tsx ----
import { Slider } from '@base-ui/react/slider';
import { createRenderer, describeConformance } from '#test-utils';

describe('<Slider.Track />', () => {
  const { render } = createRenderer();

  describeConformance(<Slider.Track />, () => ({
    render: (node) => {
      return render(<Slider.Root>{node}</Slider.Root>);
    },
    refInstanceof: window.HTMLDivElement,
  }));
});

// ---- packages/react/src/slider/utils/getPushedThumbValues.test.ts ----
import { expect } from 'vitest';
import { getPushedThumbValues } from './getPushedThumbValues';

describe('getPushedThumbValues', () => {
  it('pushes the next thumb forward when moving past it', () => {
    const result = getPushedThumbValues({
      values: [20, 40],
      index: 0,
      nextValue: 70,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(result).toEqual([70, 70]);
  });

  it('ensures minimum distance between thumbs while pushing forward', () => {
    const result = getPushedThumbValues({
      values: [20, 40],
      index: 0,
      nextValue: 60,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    expect(result).toEqual([60, 65]);
  });

  it('pushes previous thumbs backward when moving before them', () => {
    const result = getPushedThumbValues({
      values: [20, 40],
      index: 1,
      nextValue: -10,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(result).toEqual([0, 0]);
  });

  it('pushes multiple thumbs in sequence', () => {
    const result = getPushedThumbValues({
      values: [10, 50, 90],
      index: 1,
      nextValue: 95,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    expect(result).toEqual([10, 95, 100]);
  });

  it('allows fractional minimum distances', () => {
    const result = getPushedThumbValues({
      values: [0, 1],
      index: 0,
      nextValue: 1.4,
      min: 0,
      max: 10,
      step: 1,
      minStepsBetweenValues: 0.4,
    });

    expect(result[0]).toBe(1.4);
    expect(result[1]).toBe(1.8);
  });

  it('restores pushed thumbs towards their initial value when space allows', () => {
    const initialValues = [30, 50];

    const pushed = getPushedThumbValues({
      values: initialValues,
      initialValues,
      index: 1,
      nextValue: 20,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(pushed).toEqual([20, 20]);

    const restored = getPushedThumbValues({
      values: pushed,
      initialValues,
      index: 1,
      nextValue: 35,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(restored).toEqual([30, 35]);
  });
});

// ---- packages/react/src/slider/utils/resolveThumbCollision.test.ts ----
import { expect } from 'vitest';
import { resolveThumbCollision } from './resolveThumbCollision';

describe('resolveThumbCollision', () => {
  it('prevents thumbs from passing each other when behavior is "none"', () => {
    const result = resolveThumbCollision({
      behavior: 'none',
      values: [20, 40],
      pressedIndex: 0,
      nextValue: 70,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(result.value).toEqual([40, 40]);
    expect(result.thumbIndex).toBe(0);
    expect(result.didSwap).toBe(false);
  });

  it('pushes thumbs forward without cling when behavior is "push"', () => {
    const result = resolveThumbCollision({
      behavior: 'push',
      values: [20, 40],
      pressedIndex: 0,
      nextValue: 70,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(result.value).toEqual([70, 70]);
    expect(result.thumbIndex).toBe(0);
    expect(result.didSwap).toBe(false);
  });

  it('keeps pushed thumbs in place when moving backward in push mode', () => {
    const startValues = [20, 40];

    const pushed = resolveThumbCollision({
      behavior: 'push',
      values: startValues,
      currentValues: startValues,
      initialValues: startValues,
      pressedIndex: 0,
      nextValue: 70,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    const nextValues = pushed.value as number[];
    expect(nextValues).toEqual([70, 70]);

    const movedBack = resolveThumbCollision({
      behavior: 'push',
      values: nextValues,
      currentValues: nextValues,
      initialValues: startValues,
      pressedIndex: 0,
      nextValue: 30,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(movedBack.value).toEqual([30, 70]);
    expect(movedBack.thumbIndex).toBe(0);
    expect(movedBack.didSwap).toBe(false);
  });

  it('swaps thumbs when behavior is "swap"', () => {
    const result = resolveThumbCollision({
      behavior: 'swap',
      values: [20, 40],
      pressedIndex: 0,
      nextValue: 65,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 0,
    });

    expect(result.value).toEqual([40, 65]);
    expect(result.thumbIndex).toBe(1);
    expect(result.didSwap).toBe(true);
  });

  it('maintains swap continuity with minimum steps when provided current and initial values', () => {
    const startValues = [20, 80];

    const first = resolveThumbCollision({
      behavior: 'swap',
      values: startValues,
      currentValues: startValues,
      initialValues: startValues,
      pressedIndex: 0,
      nextValue: 85,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 10,
    });

    const firstValues = first.value as number[];
    expect(firstValues).toEqual([70, 85]);
    expect(first.thumbIndex).toBe(1);
    expect(first.didSwap).toBe(true);

    const continued = resolveThumbCollision({
      behavior: 'swap',
      values: startValues,
      currentValues: firstValues,
      initialValues: startValues,
      pressedIndex: first.thumbIndex,
      nextValue: 95,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 10,
    });

    const continuedValues = continued.value as number[];
    expect(continuedValues).toEqual([70, 95]);
    expect(continued.thumbIndex).toBe(1);
    expect(continued.didSwap).toBe(false);
  });

  it('does not swap before reaching neighbour value with minimum steps', () => {
    const result = resolveThumbCollision({
      behavior: 'swap',
      values: [25, 45],
      currentValues: [40, 45],
      initialValues: [25, 45],
      pressedIndex: 0,
      nextValue: 44,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    const resultValues = result.value as number[];
    expect(resultValues).toEqual([40, 45]);
    expect(result.thumbIndex).toBe(0);
    expect(result.didSwap).toBe(false);
  });

  it('swaps once reaching the neighbour value with minimum steps', () => {
    const result = resolveThumbCollision({
      behavior: 'swap',
      values: [25, 45],
      currentValues: [40, 45],
      initialValues: [25, 45],
      pressedIndex: 0,
      nextValue: 45,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    const resultValues = result.value as number[];
    expect(resultValues).toEqual([40, 45]);
    expect(result.thumbIndex).toBe(1);
    expect(result.didSwap).toBe(true);
  });

  it('does not swap backward before reaching neighbour value with minimum steps', () => {
    const result = resolveThumbCollision({
      behavior: 'swap',
      values: [25, 45],
      currentValues: [25, 40],
      initialValues: [25, 45],
      pressedIndex: 1,
      nextValue: 29,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    const resultValues = result.value as number[];
    expect(resultValues).toEqual([25, 30]);
    expect(result.thumbIndex).toBe(1);
    expect(result.didSwap).toBe(false);
  });

  it('swaps backward once reaching the neighbour value with minimum steps', () => {
    const result = resolveThumbCollision({
      behavior: 'swap',
      values: [25, 45],
      currentValues: [25, 40],
      initialValues: [25, 45],
      pressedIndex: 1,
      nextValue: 25,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    const resultValues = result.value as number[];
    expect(resultValues).toEqual([25, 30]);
    expect(result.thumbIndex).toBe(0);
    expect(result.didSwap).toBe(true);
  });

  it('does not move the clamped neighbour when swapping across with minimum steps', () => {
    const startValues = [25, 45];
    const currentValues = [40, 45];

    const result = resolveThumbCollision({
      behavior: 'swap',
      values: currentValues,
      currentValues,
      initialValues: startValues,
      pressedIndex: 0,
      nextValue: 46,
      min: 0,
      max: 100,
      step: 1,
      minStepsBetweenValues: 5,
    });

    const resultValues = result.value as number[];
    expect(resultValues).toEqual([40, 46]);
    expect(result.thumbIndex).toBe(1);
    expect(result.didSwap).toBe(true);
  });
});

// ---- packages/react/src/slider/utils/roundValueToStep.test.ts ----
import { describe, expect, it } from 'vitest';
import { roundValueToStep } from './roundValueToStep';

describe('roundValueToStep', () => {
  it('preserves precision from the step origin', () => {
    expect(roundValueToStep(0.35, 0.1, 0.25)).toBe(0.35);
  });
});

// ---- packages/react/src/slider/value/SliderValue.test.tsx ----
import { expect, vi } from 'vitest';
import { screen } from '@mui/internal-test-utils';
import { Slider } from '@base-ui/react/slider';
import { createRenderer, describeConformance } from '#test-utils';

describe('<Slider.Value />', () => {
  const { render } = createRenderer();

  describeConformance(<Slider.Value />, () => ({
    render: (node) => {
      return render(<Slider.Root>{node}</Slider.Root>);
    },
    refInstanceof: window.HTMLOutputElement,
  }));

  it('renders a single value', async () => {
    await render(
      <Slider.Root defaultValue={40}>
        <Slider.Value data-testid="output" />
      </Slider.Root>,
    );

    const sliderValue = screen.getByTestId('output');

    expect(sliderValue).toHaveTextContent('40');
  });

  it('renders a range', async () => {
    await render(
      <Slider.Root defaultValue={[40, 65]}>
        <Slider.Value data-testid="output" />
      </Slider.Root>,
    );

    const sliderValue = screen.getByTestId('output');

    expect(sliderValue).toHaveTextContent('40 – 65');
  });

  it('renders all thumb values', async () => {
    await render(
      <Slider.Root defaultValue={[40, 60, 80, 95]}>
        <Slider.Value data-testid="output" />
      </Slider.Root>,
    );

    const sliderValue = screen.getByTestId('output');

    expect(sliderValue).toHaveTextContent('40 – 60 – 80 – 95');
  });

  describe('prop: children', () => {
    it('accepts a render function', async () => {
      const format: Intl.NumberFormatOptions = {
        style: 'currency',
        currency: 'USD',
      };
      function formatValue(v: number) {
        return new Intl.NumberFormat(undefined, format).format(v);
      }
      const renderSpy = vi.fn();
      await render(
        <Slider.Root defaultValue={[40, 60]} format={format}>
          <Slider.Value data-testid="output">{renderSpy}</Slider.Value>
        </Slider.Root>,
      );

      expect(renderSpy.mock.lastCall?.[0]).toEqual([formatValue(40), formatValue(60)]);
      expect(renderSpy.mock.lastCall?.[1]).toEqual([40, 60]);
    });
  });
});

