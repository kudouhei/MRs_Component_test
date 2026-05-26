// ---- packages/react/src/drawer/content/DrawerContent.test.tsx ----
import { describe, expect, it } from 'vitest';
import { Drawer } from '@base-ui/react/drawer';
import { screen } from '@mui/internal-test-utils';
import { createRenderer, describeConformance } from '#test-utils';

describe('<Drawer.Content />', () => {
  const { render } = createRenderer();

  describeConformance(<Drawer.Content />, () => ({
    refInstanceof: window.HTMLDivElement,
    render(node) {
      return render(
        <Drawer.Root open>
          <Drawer.Portal>
            <Drawer.Viewport>
              <Drawer.Popup>{node}</Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );
    },
  }));

  it('does not add public swipe-ignore attributes', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup>
              <Drawer.Content data-testid="content">Content</Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    expect(screen.getByTestId('content')).not.toHaveAttribute('data-swipe-ignore');
    expect(screen.getByTestId('content')).not.toHaveAttribute('data-base-ui-swipe-ignore');
  });
});

// ---- packages/react/src/drawer/indent/DrawerIndent.test.tsx ----
import { describe, expect, it } from 'vitest';
import { Drawer } from '@base-ui/react/drawer';
import { screen } from '@mui/internal-test-utils';
import { createRenderer } from '#test-utils';

interface TestCaseProps {
  open: boolean;
}

function TestCase(props: TestCaseProps) {
  const { open } = props;

  return (
    <Drawer.Provider>
      <Drawer.IndentBackground data-testid="bg" />
      <Drawer.Indent data-testid="indent">
        <Drawer.Root open={open}>
          <Drawer.Trigger>Open</Drawer.Trigger>
        </Drawer.Root>
      </Drawer.Indent>
    </Drawer.Provider>
  );
}

describe('<Drawer.Indent />', () => {
  const { render } = createRenderer();

  it('sets data-active when any drawer is open', async () => {
    const { setProps } = await render(<TestCase open={false} />);

    expect(screen.getByTestId('indent')).toHaveAttribute('data-inactive', '');
    expect(screen.getByTestId('indent')).not.toHaveAttribute('data-active');

    await setProps({ open: true });

    expect(screen.getByTestId('indent')).toHaveAttribute('data-active', '');
    expect(screen.getByTestId('indent')).not.toHaveAttribute('data-inactive');
    expect(screen.getByTestId('bg')).toHaveAttribute('data-active', '');
  });
});

// ---- packages/react/src/drawer/indent-background/DrawerIndentBackground.test.tsx ----
import { expect } from 'vitest';
import { Drawer } from '@base-ui/react/drawer';
import { screen } from '@mui/internal-test-utils';
import { createRenderer } from '#test-utils';

interface TestCaseProps {
  open: boolean;
}

function TestCase(props: TestCaseProps) {
  const { open } = props;

  return (
    <Drawer.Provider>
      <Drawer.IndentBackground data-testid="bg" />
      <Drawer.Root open={open}>
        <Drawer.Trigger>Open</Drawer.Trigger>
      </Drawer.Root>
    </Drawer.Provider>
  );
}

describe('<Drawer.IndentBackground />', () => {
  const { render } = createRenderer();

  it('sets data-active when any drawer is open', async () => {
    const { setProps } = await render(<TestCase open={false} />);

    const background = screen.getByTestId('bg');

    expect(background.getAttribute('data-inactive')).toBe('');
    expect(background.getAttribute('data-active')).toBeNull();

    await setProps({ open: true });

    expect(background.getAttribute('data-active')).toBe('');
    expect(background.getAttribute('data-inactive')).toBeNull();
  });
});

// ---- packages/react/src/drawer/popup/DrawerPopup.test.tsx ----
import { describe, expect, it, vi } from 'vitest';
import * as React from 'react';
import { AlertDialog } from '@base-ui/react/alert-dialog';
import { Dialog } from '@base-ui/react/dialog';
import { Drawer } from '@base-ui/react/drawer';
import { act, screen, waitFor } from '@mui/internal-test-utils';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';

describe('<Drawer.Popup />', () => {
  const { render } = createRenderer();

  describeConformance(<Drawer.Popup />, () => ({
    refInstanceof: window.HTMLDivElement,
    render(node) {
      return render(
        <Drawer.Root open>
          <Drawer.Portal>
            <Drawer.Viewport>{node}</Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );
    },
  }));

  it('warns in development when not rendered within a viewport', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Popup>Drawer</Drawer.Popup>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining(
          'Base UI: <Drawer.Popup> expected to be rendered within <Drawer.Viewport>.',
        ),
      );
    });

    consoleErrorSpy.mockRestore();
  });

  it('defaults initial focus to the popup element', async () => {
    await render(
      <div>
        <input />
        <Drawer.Root modal={false}>
          <Drawer.Trigger>Open</Drawer.Trigger>
          <Drawer.Portal>
            <Drawer.Viewport>
              <Drawer.Popup data-testid="popup">
                <input data-testid="popup-input" />
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>
      </div>,
    );

    await act(async () => {
      screen.getByRole('button', { name: 'Open' }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('popup')).toHaveFocus();
      expect(screen.getByTestId('popup-input')).not.toHaveFocus();
    });
  });

  it.skipIf(isJSDOM)(
    'includes border size in frontmost height CSS variable for nested drawers',
    async () => {
      await render(
        <Drawer.Root open>
          <Drawer.Portal>
            <Drawer.Viewport>
              <Drawer.Popup data-testid="parent-popup">
                <Drawer.Root open>
                  <Drawer.Portal>
                    <Drawer.Viewport>
                      <Drawer.Popup
                        data-testid="child-popup"
                        style={{
                          height: 100,
                          borderTop: '2px solid transparent',
                          borderBottom: '2px solid transparent',
                        }}
                      >
                        <div style={{ height: 10 }}>Child drawer</div>
                      </Drawer.Popup>
                    </Drawer.Viewport>
                  </Drawer.Portal>
                </Drawer.Root>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const parentPopup = screen.getByTestId('parent-popup');
      const childPopup = screen.getByTestId('child-popup');

      await waitFor(() => {
        expect(childPopup.offsetHeight).toBeGreaterThan(childPopup.scrollHeight);
        expect(parentPopup.style.getPropertyValue('--drawer-frontmost-height')).toBe(
          `${childPopup.offsetHeight}px`,
        );
      });
    },
  );

  it('does not treat dialogs inside nested drawers as nested drawers', async () => {
    await render(
      <Drawer.Root open modal={false}>
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="parent-popup">
              <Drawer.Root open modal={false}>
                <Drawer.Portal>
                  <Drawer.Viewport>
                    <Drawer.Popup data-testid="child-popup">
                      <Dialog.Root modal={false}>
                        <Dialog.Trigger>Open dialog</Dialog.Trigger>
                        <Dialog.Portal>
                          <Dialog.Popup data-testid="dialog-popup">Dialog</Dialog.Popup>
                        </Dialog.Portal>
                      </Dialog.Root>
                    </Drawer.Popup>
                  </Drawer.Viewport>
                </Drawer.Portal>
              </Drawer.Root>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const parentPopup = screen.getByTestId('parent-popup');
    const childPopup = screen.getByTestId('child-popup');
    const observedNestedDrawerCounts = [parentPopup.style.getPropertyValue('--nested-drawers')];

    const observer = new MutationObserver(() => {
      observedNestedDrawerCounts.push(parentPopup.style.getPropertyValue('--nested-drawers'));
    });

    observer.observe(parentPopup, {
      attributeFilter: ['style'],
      attributes: true,
    });

    await waitFor(() => {
      expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('1');
    });
    expect(childPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
    expect(childPopup).not.toHaveAttribute('data-nested-drawer-open');

    await act(async () => {
      screen.getByRole('button', { name: 'Open dialog' }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('dialog-popup')).toBeVisible();
    });
    await waitFor(() => {
      expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('1');
    });
    expect(childPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
    expect(childPopup).not.toHaveAttribute('data-nested-drawer-open');

    observer.disconnect();

    expect(observedNestedDrawerCounts).not.toContain('2');
  });

  it('does not treat alert dialogs inside nested drawers as nested drawers', async () => {
    await render(
      <Drawer.Root open modal={false}>
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="parent-popup">
              <Drawer.Root open modal={false}>
                <Drawer.Portal>
                  <Drawer.Viewport>
                    <Drawer.Popup data-testid="child-popup">
                      <AlertDialog.Root>
                        <AlertDialog.Trigger>Open alert dialog</AlertDialog.Trigger>
                        <AlertDialog.Portal>
                          <AlertDialog.Popup data-testid="alert-dialog-popup">
                            Alert dialog
                            <AlertDialog.Close>Close alert dialog</AlertDialog.Close>
                          </AlertDialog.Popup>
                        </AlertDialog.Portal>
                      </AlertDialog.Root>
                    </Drawer.Popup>
                  </Drawer.Viewport>
                </Drawer.Portal>
              </Drawer.Root>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const parentPopup = screen.getByTestId('parent-popup');
    const childPopup = screen.getByTestId('child-popup');
    const observedNestedDrawerCounts = [parentPopup.style.getPropertyValue('--nested-drawers')];

    const observer = new MutationObserver(() => {
      observedNestedDrawerCounts.push(parentPopup.style.getPropertyValue('--nested-drawers'));
    });

    observer.observe(parentPopup, {
      attributeFilter: ['style'],
      attributes: true,
    });

    await waitFor(() => {
      expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('1');
    });
    expect(childPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
    expect(childPopup).not.toHaveAttribute('data-nested-drawer-open');

    await act(async () => {
      screen.getByRole('button', { name: 'Open alert dialog' }).click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('alert-dialog-popup')).toBeVisible();
    });
    await waitFor(() => {
      expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('1');
    });
    expect(childPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
    expect(childPopup).not.toHaveAttribute('data-nested-drawer-open');

    observer.disconnect();

    expect(observedNestedDrawerCounts).not.toContain('2');
  });

  it('clears parent nested drawer state as soon as a nested drawer closes', async () => {
    await render(
      <Drawer.Root open modal={false}>
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="parent-popup">
              <Drawer.Root modal={false}>
                <Drawer.Trigger>Open nested drawer</Drawer.Trigger>
                <Drawer.Portal keepMounted>
                  <Drawer.Viewport>
                    <Drawer.Popup data-testid="child-popup">
                      <Drawer.Close>Close nested drawer</Drawer.Close>
                    </Drawer.Popup>
                  </Drawer.Viewport>
                </Drawer.Portal>
              </Drawer.Root>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const parentPopup = screen.getByTestId('parent-popup');
    const childPopup = screen.getByTestId('child-popup');

    expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
    expect(parentPopup).not.toHaveAttribute('data-nested-drawer-open');

    await act(async () => {
      screen.getByRole('button', { name: 'Open nested drawer' }).click();
    });

    await waitFor(() => {
      expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('1');
    });
    expect(parentPopup).toHaveAttribute('data-nested-drawer-open', '');

    await act(async () => {
      screen.getByRole('button', { name: 'Close nested drawer' }).click();
    });

    expect(childPopup).toBeInTheDocument();
    expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
    expect(parentPopup).not.toHaveAttribute('data-nested-drawer-open');
  });

  it.skipIf(isJSDOM)(
    'clears parent nested drawer state when a nested drawer starts closing before unmount',
    async () => {
      globalThis.BASE_UI_ANIMATIONS_DISABLED = false;

      const style = `
        @keyframes test-drawer-exit {
          to {
            opacity: 0;
          }
        }

        .animation-test-child-popup[data-ending-style] {
          animation: test-drawer-exit 100ms;
        }
      `;

      try {
        await render(
          <div>
            {/* eslint-disable-next-line react/no-danger */}
            <style dangerouslySetInnerHTML={{ __html: style }} />
            <Drawer.Root open modal={false}>
              <Drawer.Portal>
                <Drawer.Viewport>
                  <Drawer.Popup data-testid="parent-popup">
                    <Drawer.Root defaultOpen modal={false}>
                      <Drawer.Portal>
                        <Drawer.Viewport>
                          <Drawer.Popup
                            className="animation-test-child-popup"
                            data-testid="child-popup"
                          >
                            <Drawer.Close>Close nested drawer</Drawer.Close>
                          </Drawer.Popup>
                        </Drawer.Viewport>
                      </Drawer.Portal>
                    </Drawer.Root>
                  </Drawer.Popup>
                </Drawer.Viewport>
              </Drawer.Portal>
            </Drawer.Root>
          </div>,
        );

        const parentPopup = screen.getByTestId('parent-popup');

        await waitFor(() => {
          expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('1');
        });
        expect(parentPopup).toHaveAttribute('data-nested-drawer-open', '');

        await act(async () => {
          screen.getByRole('button', { name: 'Close nested drawer' }).click();
        });

        await waitFor(() => {
          expect(screen.getByTestId('child-popup')).toHaveAttribute('data-ending-style');
        });
        expect(parentPopup.style.getPropertyValue('--nested-drawers')).toBe('0');
        expect(parentPopup).not.toHaveAttribute('data-nested-drawer-open');

        await waitFor(() => {
          expect(screen.queryByTestId('child-popup')).toBeNull();
        });
      } finally {
        globalThis.BASE_UI_ANIMATIONS_DISABLED = true;
      }
    },
  );

  it.skipIf(isJSDOM)('keeps a fixed height applied while a nested drawer closes', async () => {
    globalThis.BASE_UI_ANIMATIONS_DISABLED = false;

    const style = `
        @keyframes test-drawer-exit {
          to {
            opacity: 0;
          }
        }

        .animation-test-parent-popup {
          height: var(--drawer-height, auto);
          overflow: hidden;
          transition: height 100ms linear;
        }

        .animation-test-parent-popup[data-nested-drawer-open] {
          height: var(--drawer-frontmost-height, var(--drawer-height));
        }

        .animation-test-parent-content {
          display: block;
          height: 160px;
        }

        .animation-test-child-content {
          display: block;
          height: 64px;
        }

        .animation-test-child-popup[data-ending-style] {
          animation: test-drawer-exit 100ms;
        }
      `;

    try {
      await render(
        <div>
          {/* eslint-disable-next-line react/no-danger */}
          <style dangerouslySetInnerHTML={{ __html: style }} />
          <Drawer.Root open modal={false}>
            <Drawer.Portal>
              <Drawer.Viewport>
                <Drawer.Popup className="animation-test-parent-popup" data-testid="parent-popup">
                  <div className="animation-test-parent-content" />
                  <Drawer.Root modal={false}>
                    <Drawer.Trigger>Open nested drawer</Drawer.Trigger>
                    <Drawer.Portal>
                      <Drawer.Viewport>
                        <Drawer.Popup
                          className="animation-test-child-popup"
                          data-testid="child-popup"
                        >
                          <div className="animation-test-child-content" />
                          <Drawer.Close>Close nested drawer</Drawer.Close>
                        </Drawer.Popup>
                      </Drawer.Viewport>
                    </Drawer.Portal>
                  </Drawer.Root>
                </Drawer.Popup>
              </Drawer.Viewport>
            </Drawer.Portal>
          </Drawer.Root>
        </div>,
      );

      const parentPopup = screen.getByTestId('parent-popup');
      await act(async () => {
        screen.getByRole('button', { name: 'Open nested drawer' }).click();
      });

      await waitFor(() => {
        expect(parentPopup).toHaveAttribute('data-nested-drawer-open', '');
      });
      await waitFor(() => {
        expect(parentPopup.style.getPropertyValue('--drawer-height')).not.toBe('');
      });

      const mutations: Array<{ hasNested: boolean; drawerHeight: string }> = [];
      const observer = new MutationObserver(() => {
        mutations.push({
          hasNested: parentPopup.hasAttribute('data-nested-drawer-open'),
          drawerHeight: parentPopup.style.getPropertyValue('--drawer-height'),
        });
      });

      observer.observe(parentPopup, {
        attributeFilter: ['data-nested-drawer-open', 'style'],
        attributes: true,
      });

      await act(async () => {
        screen.getByRole('button', { name: 'Close nested drawer' }).click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('child-popup')).toHaveAttribute('data-ending-style');
      });
      await waitFor(() => {
        expect(parentPopup).not.toHaveAttribute('data-nested-drawer-open');
      });
      await waitFor(() => {
        expect(parentPopup.style.getPropertyValue('--drawer-height')).not.toBe('');
      });
      await waitFor(() => {
        expect(
          mutations.some((mutation) => !mutation.hasNested && mutation.drawerHeight !== ''),
        ).toBe(true);
      });

      observer.disconnect();

      await waitFor(() => {
        expect(screen.queryByTestId('child-popup')).toBeNull();
      });
    } finally {
      globalThis.BASE_UI_ANIMATIONS_DISABLED = true;
    }
  });

  it.skipIf(isJSDOM)(
    'restores a fixed height before nested state when reopening a nested drawer',
    async () => {
      globalThis.BASE_UI_ANIMATIONS_DISABLED = false;

      const style = `
        .animation-test-parent-popup {
          height: var(--drawer-height, auto);
          overflow: hidden;
          transition: height 100ms linear;
        }

        .animation-test-parent-popup[data-nested-drawer-open] {
          height: var(--drawer-frontmost-height, var(--drawer-height));
        }

        .animation-test-parent-content {
          display: block;
          height: 160px;
        }

        .animation-test-child-content {
          display: block;
          height: 64px;
        }
      `;

      try {
        await render(
          <div>
            {/* eslint-disable-next-line react/no-danger */}
            <style dangerouslySetInnerHTML={{ __html: style }} />
            <Drawer.Root open modal={false}>
              <Drawer.Portal>
                <Drawer.Viewport>
                  <Drawer.Popup className="animation-test-parent-popup" data-testid="parent-popup">
                    <div className="animation-test-parent-content" />
                    <Drawer.Root modal={false}>
                      <Drawer.Trigger>Open nested drawer</Drawer.Trigger>
                      <Drawer.Portal>
                        <Drawer.Viewport>
                          <Drawer.Popup data-testid="child-popup">
                            <div className="animation-test-child-content" />
                            <Drawer.Close>Close nested drawer</Drawer.Close>
                          </Drawer.Popup>
                        </Drawer.Viewport>
                      </Drawer.Portal>
                    </Drawer.Root>
                  </Drawer.Popup>
                </Drawer.Viewport>
              </Drawer.Portal>
            </Drawer.Root>
          </div>,
        );

        const parentPopup = screen.getByTestId('parent-popup');
        await act(async () => {
          screen.getByRole('button', { name: 'Open nested drawer' }).click();
        });

        await waitFor(() => {
          expect(parentPopup).toHaveAttribute('data-nested-drawer-open', '');
        });

        await act(async () => {
          screen.getByRole('button', { name: 'Close nested drawer' }).click();
        });

        await waitFor(() => {
          expect(parentPopup).not.toHaveAttribute('data-nested-drawer-open');
        });
        await waitFor(() => {
          expect(screen.queryByTestId('child-popup')).toBeNull();
        });

        const mutations: Array<{ hasNested: boolean; drawerHeight: string }> = [];
        const observer = new MutationObserver(() => {
          mutations.push({
            hasNested: parentPopup.hasAttribute('data-nested-drawer-open'),
            drawerHeight: parentPopup.style.getPropertyValue('--drawer-height'),
          });
        });

        observer.observe(parentPopup, {
          attributeFilter: ['data-nested-drawer-open', 'style'],
          attributes: true,
        });

        await act(async () => {
          screen.getByRole('button', { name: 'Open nested drawer' }).click();
        });

        await waitFor(() => {
          expect(parentPopup).toHaveAttribute('data-nested-drawer-open', '');
        });
        await waitFor(() => {
          expect(mutations.find((mutation) => mutation.hasNested)?.drawerHeight).not.toBe('');
        });
        observer.disconnect();
      } finally {
        globalThis.BASE_UI_ANIMATIONS_DISABLED = true;
      }
    },
  );
});

// ---- packages/react/src/drawer/root/DrawerRoot.test.tsx ----
import { beforeAll, describe, expect, it, vi } from 'vitest';
import * as React from 'react';
import { Drawer } from '@base-ui/react/drawer';
import { act, fireEvent, flushMicrotasks, screen } from '@mui/internal-test-utils';
import { createRenderer, isJSDOM, waitSingleFrame } from '#test-utils';
import { REASONS } from '../../internals/reasons';
import { useDrawerRootContext } from './DrawerRootContext';

vi.mock('@base-ui/utils/detectBrowser', async () => {
  const actual = await vi.importActual<typeof import('@base-ui/utils/detectBrowser')>(
    '@base-ui/utils/detectBrowser',
  );
  return { ...actual, isAndroid: true };
});

function TestCase({ onOpenChange }: { onOpenChange: (open: boolean) => void }) {
  const [open, setOpen] = React.useState(true);

  return (
    <Drawer.Root
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);
        onOpenChange(nextOpen);
      }}
      swipeDirection="right"
    >
      <Drawer.Portal>
        <Drawer.Viewport data-testid="viewport">
          <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
        </Drawer.Viewport>
      </Drawer.Portal>
    </Drawer.Root>
  );
}

async function simulateTimedRightSwipe(
  element: HTMLElement,
  startX: number,
  endX: number,
  startTime: number,
  moveTime: number,
  endTime: number,
) {
  if (isJSDOM) {
    vi.setSystemTime(new Date(startTime));
    fireEvent.pointerDown(element, {
      button: 0,
      buttons: 1,
      pointerId: 1,
      clientX: startX,
      clientY: 100,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    vi.setSystemTime(new Date(moveTime));
    fireEvent.pointerMove(element, {
      pointerId: 1,
      clientX: startX + 1,
      clientY: 100,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    vi.setSystemTime(new Date(endTime - 1));
    fireEvent.pointerMove(element, {
      pointerId: 1,
      clientX: endX,
      clientY: 100,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    vi.setSystemTime(new Date(endTime));
    fireEvent.pointerUp(element, {
      pointerId: 1,
      clientX: endX,
      clientY: 100,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();
    return;
  }

  const moveDelay = Math.max(0, moveTime - startTime);
  const endDelay = Math.max(0, endTime - moveTime);

  fireEvent.pointerDown(element, {
    button: 0,
    buttons: 1,
    pointerId: 1,
    clientX: startX,
    clientY: 100,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();
  await new Promise((resolve) => {
    setTimeout(resolve, moveDelay);
  });

  fireEvent.pointerMove(element, {
    pointerId: 1,
    clientX: startX + 1,
    clientY: 100,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();
  await new Promise((resolve) => {
    setTimeout(resolve, endDelay);
  });

  fireEvent.pointerMove(element, {
    pointerId: 1,
    clientX: endX,
    clientY: 100,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();

  fireEvent.pointerUp(element, {
    pointerId: 1,
    clientX: endX,
    clientY: 100,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();
}

async function simulateTimedDownSwipe(
  element: HTMLElement,
  startY: number,
  endY: number,
  startTime: number,
  moveTime: number,
  endTime: number,
  settleTime?: number,
) {
  const resolvedSettleTime =
    typeof settleTime === 'number' && Number.isFinite(settleTime) ? settleTime : null;
  const settleY = endY - 1;

  if (isJSDOM) {
    vi.setSystemTime(new Date(startTime));
    fireEvent.pointerDown(element, {
      button: 0,
      buttons: 1,
      pointerId: 1,
      clientX: 100,
      clientY: startY,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    vi.setSystemTime(new Date(moveTime));
    fireEvent.pointerMove(element, {
      pointerId: 1,
      clientX: 100,
      clientY: startY + 1,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    if (resolvedSettleTime !== null) {
      vi.setSystemTime(new Date(resolvedSettleTime));
      fireEvent.pointerMove(element, {
        pointerId: 1,
        clientX: 100,
        clientY: settleY,
        bubbles: true,
        pointerType: 'mouse',
      });

      await flushMicrotasks();
    }

    vi.setSystemTime(new Date(endTime - 1));
    fireEvent.pointerMove(element, {
      pointerId: 1,
      clientX: 100,
      clientY: endY,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    vi.setSystemTime(new Date(endTime));
    fireEvent.pointerUp(element, {
      pointerId: 1,
      clientX: 100,
      clientY: endY,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();
    return;
  }

  const moveDelay = Math.max(0, moveTime - startTime);
  const settleDelay =
    resolvedSettleTime !== null ? Math.max(0, resolvedSettleTime - moveTime) : null;
  const endDelay =
    resolvedSettleTime !== null
      ? Math.max(0, endTime - resolvedSettleTime)
      : Math.max(0, endTime - moveTime);

  fireEvent.pointerDown(element, {
    button: 0,
    buttons: 1,
    pointerId: 1,
    clientX: 100,
    clientY: startY,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();
  await new Promise((resolve) => {
    setTimeout(resolve, moveDelay);
  });

  fireEvent.pointerMove(element, {
    pointerId: 1,
    clientX: 100,
    clientY: startY + 1,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();

  if (settleDelay !== null) {
    await new Promise((resolve) => {
      setTimeout(resolve, settleDelay);
    });

    fireEvent.pointerMove(element, {
      pointerId: 1,
      clientX: 100,
      clientY: settleY,
      bubbles: true,
      pointerType: 'mouse',
    });

    await flushMicrotasks();
  }

  await new Promise((resolve) => {
    setTimeout(resolve, endDelay);
  });

  fireEvent.pointerMove(element, {
    pointerId: 1,
    clientX: 100,
    clientY: endY,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();

  fireEvent.pointerUp(element, {
    pointerId: 1,
    clientX: 100,
    clientY: endY,
    bubbles: true,
    pointerType: 'mouse',
  });

  await flushMicrotasks();
}

type TimedSwipeStep = {
  type: 'down' | 'move' | 'up';
  x: number;
  y: number;
  time: number;
};

async function simulateTimedSwipe(element: HTMLElement, steps: TimedSwipeStep[]) {
  if (steps.length === 0) {
    return;
  }

  function fireStep(step: TimedSwipeStep) {
    const baseEvent = {
      pointerId: 1,
      clientX: step.x,
      clientY: step.y,
      bubbles: true,
      pointerType: 'mouse',
    };

    if (step.type === 'down') {
      fireEvent.pointerDown(element, { ...baseEvent, button: 0, buttons: 1 });
      return;
    }

    if (step.type === 'move') {
      fireEvent.pointerMove(element, baseEvent);
      return;
    }

    fireEvent.pointerUp(element, baseEvent);
  }

  if (isJSDOM) {
    await steps.reduce(async (previous, step) => {
      await previous;
      vi.setSystemTime(new Date(step.time));
      fireStep(step);
      await flushMicrotasks();
    }, Promise.resolve());
    return;
  }

  await steps.reduce(async (previous, step, index) => {
    await previous;
    const previousTime = steps[index - 1]?.time ?? step.time;
    const delay = index === 0 ? 0 : Math.max(0, step.time - previousTime);
    if (delay > 0) {
      await new Promise((resolve) => {
        setTimeout(resolve, delay);
      });
    }

    fireStep(step);
    await flushMicrotasks();
  }, Promise.resolve());
}

function mockResizeObserver() {
  const original = globalThis.ResizeObserver;
  if (typeof original === 'function') {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    } as typeof ResizeObserver;
  }
  return () => {
    if (typeof original === 'function') {
      globalThis.ResizeObserver = original;
    }
  };
}

/**
 * Sets up `elementFromPoint` and `ResizeObserver` mocks for swipe-dismiss tests.
 * Returns a cleanup function that restores originals.
 */
function setupSwipeTestEnv() {
  const originalElementFromPoint = document.elementFromPoint;
  const restoreResizeObserver = mockResizeObserver();
  return {
    /** Call after rendering to point `elementFromPoint` at the given element. */
    pointAt(element: Element) {
      document.elementFromPoint = () => element;
    },
    cleanup() {
      document.elementFromPoint = originalElementFromPoint;
      restoreResizeObserver();
    },
  };
}

function SnapPointResetCase() {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[2]);

  return (
    <div>
      <div data-testid="active-snap">{String(snapPoint)}</div>
      <Drawer.Root
        open={open}
        onOpenChange={setOpen}
        snapPoints={snapPoints}
        snapPoint={snapPoint}
        onSnapPointChange={setSnapPoint}
      >
        <Drawer.Portal>
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              Drawer
              <Drawer.Close data-testid="close">Close</Drawer.Close>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

function ActiveSnapPointDisplay() {
  const { activeSnapPoint } = useDrawerRootContext();
  return <div data-testid="active-snap">{String(activeSnapPoint)}</div>;
}

function DefaultSnapPointResetCase() {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);

  return (
    <Drawer.Root
      defaultSnapPoint={snapPoints[1]}
      open={open}
      onOpenChange={setOpen}
      snapPoints={snapPoints}
    >
      <ActiveSnapPointDisplay />
      <Drawer.Portal>
        <Drawer.Viewport data-testid="viewport">
          <Drawer.Popup data-testid="popup">
            Drawer
            <Drawer.Close data-testid="close">Close</Drawer.Close>
          </Drawer.Popup>
        </Drawer.Viewport>
      </Drawer.Portal>
    </Drawer.Root>
  );
}

function SnapPointChangeDetailsCase({
  onSnapPointChange,
}: {
  onSnapPointChange: (
    snapPoint: Drawer.Root.SnapPoint | null,
    eventDetails: Drawer.Root.SnapPointChangeEventDetails,
  ) => void;
}) {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[2]);

  return (
    <Drawer.Root
      open={open}
      onOpenChange={setOpen}
      snapPoints={snapPoints}
      snapPoint={snapPoint}
      onSnapPointChange={(nextSnapPoint, eventDetails) => {
        setSnapPoint(nextSnapPoint);
        onSnapPointChange(nextSnapPoint, eventDetails);
      }}
    >
      <Drawer.Portal>
        <Drawer.Viewport data-testid="viewport">
          <Drawer.Popup data-testid="popup">
            Drawer
            <Drawer.Close data-testid="close">Close</Drawer.Close>
          </Drawer.Popup>
        </Drawer.Viewport>
      </Drawer.Portal>
    </Drawer.Root>
  );
}

function CanceledCloseSnapPointResetCase() {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[2]);

  return (
    <div>
      <div data-testid="active-snap">{String(snapPoint)}</div>
      <Drawer.Root
        open={open}
        onOpenChange={(nextOpen, eventDetails) => {
          if (!nextOpen) {
            eventDetails.cancel();
          } else {
            setOpen(nextOpen);
          }
        }}
        snapPoints={snapPoints}
        snapPoint={snapPoint}
        onSnapPointChange={setSnapPoint}
      >
        <Drawer.Portal>
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              Drawer
              <Drawer.Close data-testid="close">Close</Drawer.Close>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

function ControlledAlwaysOpenCase({
  onOpenChange,
}: {
  onOpenChange?: (open: boolean, eventDetails: Drawer.Root.ChangeEventDetails) => void;
}) {
  return (
    <Drawer.Root open onOpenChange={onOpenChange} swipeDirection="down">
      <Drawer.Portal>
        <Drawer.Backdrop data-testid="backdrop" />
        <Drawer.Viewport data-testid="viewport" style={{ height: 300 }}>
          <Drawer.Popup data-testid="popup" style={{ height: 200 }}>
            Drawer
          </Drawer.Popup>
        </Drawer.Viewport>
      </Drawer.Portal>
    </Drawer.Root>
  );
}

function ControlledSwipeCloseSnapPointCase() {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);
  // Start at '300px' (non-default) so we can distinguish correct reset to
  // the default ('100px') from incorrect restoration to the pre-swipe value.
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[1]);

  return (
    <div>
      <div data-testid="active-snap">{String(snapPoint)}</div>
      <Drawer.Root
        open={open}
        onOpenChange={setOpen}
        snapPoints={snapPoints}
        snapPoint={snapPoint}
        onSnapPointChange={setSnapPoint}
        swipeDirection="down"
      >
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport" style={{ height: 600 }}>
            <Drawer.Popup data-testid="popup" style={{ height: 600 }}>
              Drawer
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

function CanceledSwipeCloseCase() {
  const [open, setOpen] = React.useState(true);

  return (
    <Drawer.Root
      open={open}
      onOpenChange={(nextOpen, eventDetails) => {
        if (!nextOpen && eventDetails.reason === REASONS.swipe) {
          eventDetails.cancel();
          return;
        }

        setOpen(nextOpen);
      }}
      swipeDirection="down"
    >
      <Drawer.Portal>
        <Drawer.Backdrop data-testid="backdrop" />
        <Drawer.Viewport data-testid="viewport" style={{ height: 300 }}>
          <Drawer.Popup data-testid="popup" style={{ height: 200 }}>
            Drawer
          </Drawer.Popup>
        </Drawer.Viewport>
      </Drawer.Portal>
    </Drawer.Root>
  );
}

function CanceledSwipeCloseSnapPointCase() {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[0]);

  return (
    <div>
      <div data-testid="active-snap">{String(snapPoint)}</div>
      <Drawer.Root
        open={open}
        onOpenChange={(nextOpen, eventDetails) => {
          if (!nextOpen && eventDetails.reason === REASONS.swipe) {
            eventDetails.cancel();
            return;
          }

          setOpen(nextOpen);
        }}
        snapPoints={snapPoints}
        snapPoint={snapPoint}
        onSnapPointChange={setSnapPoint}
        swipeDirection="down"
      >
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport" style={{ height: 600 }}>
            <Drawer.Popup data-testid="popup" style={{ height: 600 }}>
              Drawer
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

function SnapPointSwipeCase({ onOpenChange }: { onOpenChange: (open: boolean) => void }) {
  const snapPoints = ['100px', '300px', 1];
  const [open, setOpen] = React.useState(true);
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[0]);

  return (
    <div>
      <div data-testid="active-snap">{String(snapPoint)}</div>
      <Drawer.Root
        open={open}
        onOpenChange={(nextOpen) => {
          setOpen(nextOpen);
          onOpenChange(nextOpen);
        }}
        snapPoints={snapPoints}
        snapPoint={snapPoint}
        onSnapPointChange={setSnapPoint}
        swipeDirection="down"
      >
        <Drawer.Portal>
          <Drawer.Viewport data-testid="viewport" style={{ height: 600 }}>
            <Drawer.Popup data-testid="popup" style={{ height: 600 }}>
              Drawer
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

function SnapPointSequentialSkipCase() {
  const snapPoints = ['100px', '300px', 1];
  const [snapPoint, setSnapPoint] = React.useState<Drawer.Root.SnapPoint | null>(snapPoints[0]);

  return (
    <div>
      <div data-testid="active-snap">{String(snapPoint)}</div>
      <Drawer.Root
        open
        snapPoints={snapPoints}
        snapPoint={snapPoint}
        onSnapPointChange={setSnapPoint}
        swipeDirection="down"
        snapToSequentialPoints
      >
        <Drawer.Portal>
          <Drawer.Viewport data-testid="viewport" style={{ height: 600 }}>
            <Drawer.Popup data-testid="popup" style={{ height: 600 }}>
              Drawer
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}

describe('<Drawer.Root />', () => {
  const { render } = createRenderer();

  beforeAll(function beforeHook() {
    // PointerEvent not fully implemented in jsdom, causing fireEvent.pointer* to ignore options.
    // https://github.com/jsdom/jsdom/issues/2527
    (window as any).PointerEvent = window.MouseEvent;
  });

  it.skipIf(isJSDOM)('uses a size-based swipe threshold', async () => {
    const handleOpenChange = vi.fn();
    await render(<TestCase onOpenChange={handleOpenChange} />);

    await flushMicrotasks();

    const viewport = screen.getByTestId('viewport');
    const popup = screen.getByTestId('popup');

    popup.style.width = '200px';
    await flushMicrotasks();

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    const useFakeTimers = isJSDOM;
    if (useFakeTimers) {
      vi.useFakeTimers();
    }

    try {
      const startTime = 1000;
      const moveTime = 1100;
      const endTime = 1600;

      await simulateTimedRightSwipe(viewport, 100, 190, startTime, moveTime, endTime);
      expect(handleOpenChange).not.toHaveBeenCalled();

      await simulateTimedRightSwipe(
        viewport,
        100,
        220,
        startTime + 1000,
        moveTime + 1000,
        endTime + 1000,
      );
      expect(handleOpenChange).toHaveBeenCalledWith(false);
    } finally {
      if (useFakeTimers) {
        vi.useRealTimers();
      }
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('supports detached triggers with handles', async () => {
    const handle = Drawer.createHandle<number>();

    await render(
      <div>
        <Drawer.Trigger handle={handle} payload={1}>
          Trigger 1
        </Drawer.Trigger>
        <Drawer.Trigger handle={handle} payload={2}>
          Trigger 2
        </Drawer.Trigger>
        <Drawer.Root handle={handle}>
          {({ payload }: { payload: number | undefined }) => (
            <Drawer.Portal>
              <Drawer.Viewport>
                <Drawer.Popup>
                  <span data-testid="payload">{payload}</span>
                  <Drawer.Close>Close</Drawer.Close>
                </Drawer.Popup>
              </Drawer.Viewport>
            </Drawer.Portal>
          )}
        </Drawer.Root>
      </div>,
    );

    await flushMicrotasks();
    expect(screen.queryByTestId('payload')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Trigger 1' }));
    await flushMicrotasks();
    expect(screen.getByTestId('payload').textContent).toBe('1');

    fireEvent.click(screen.getByText('Close'));
    await flushMicrotasks();
    expect(screen.queryByTestId('payload')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Trigger 2' }));
    await flushMicrotasks();
    expect(screen.getByTestId('payload').textContent).toBe('2');
  });

  it('resets the active snap point when closing', async () => {
    await render(<SnapPointResetCase />);
    await flushMicrotasks();

    const closeButton = screen.getByTestId('close');
    fireEvent.click(closeButton);

    await flushMicrotasks();

    expect(screen.getByTestId('active-snap').textContent).toBe('100px');
  });

  it('resets to the default snap point when provided', async () => {
    await render(<DefaultSnapPointResetCase />);
    await flushMicrotasks();

    expect(screen.getByTestId('active-snap').textContent).toBe('300px');

    const closeButton = screen.getByTestId('close');
    fireEvent.click(closeButton);

    await flushMicrotasks();

    expect(screen.getByTestId('active-snap').textContent).toBe('300px');
  });

  it('provides event details when snap point changes', async () => {
    const handleSnapPointChange = vi.fn();
    await render(<SnapPointChangeDetailsCase onSnapPointChange={handleSnapPointChange} />);
    await flushMicrotasks();

    const closeButton = screen.getByTestId('close');
    fireEvent.click(closeButton);

    await flushMicrotasks();

    expect(handleSnapPointChange).toHaveBeenCalled();
    const [, eventDetails] = handleSnapPointChange.mock.calls[0];
    expect(eventDetails.reason).toBe(REASONS.closePress);
  });

  it('does not reset snap point when a close is canceled', async () => {
    await render(<CanceledCloseSnapPointResetCase />);
    await flushMicrotasks();

    expect(screen.getByTestId('active-snap').textContent).toBe('1');

    fireEvent.click(screen.getByTestId('close'));
    await flushMicrotasks();

    expect(screen.getByTestId('active-snap').textContent).toBe('1');
  });

  it.skipIf(isJSDOM)('clears swipe-dismiss styles when swipe close is canceled', async () => {
    const env = setupSwipeTestEnv();

    try {
      await render(<CanceledSwipeCloseCase />);
      await flushMicrotasks();

      const viewport = screen.getByTestId('viewport');
      const popup = screen.getByTestId('popup');
      const backdrop = screen.getByTestId('backdrop');

      Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });

      env.pointAt(popup);

      await simulateTimedDownSwipe(viewport, 100, 250, 1000, 1010, 1040);

      expect(popup).not.toHaveAttribute('data-swipe-dismiss');
      expect(backdrop).not.toHaveAttribute('data-swipe-dismiss');
      expect(popup).not.toHaveAttribute('data-ending-style');
      expect(backdrop).not.toHaveAttribute('data-swiping');
      expect(popup).toHaveAttribute('data-open', '');
      expect(popup.style.getPropertyValue('--drawer-swipe-movement-y')).toBe('0px');
    } finally {
      env.cleanup();
    }
  });

  it.skipIf(isJSDOM)(
    'does not dismiss a controlled drawer via swipe when open is always true',
    async () => {
      const handleOpenChange = vi.fn();
      const env = setupSwipeTestEnv();

      try {
        await render(<ControlledAlwaysOpenCase onOpenChange={handleOpenChange} />);
        await flushMicrotasks();

        const viewport = screen.getByTestId('viewport');
        const popup = screen.getByTestId('popup');
        const backdrop = screen.getByTestId('backdrop');

        Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });

        env.pointAt(popup);

        await simulateTimedDownSwipe(viewport, 100, 250, 1000, 1010, 1040);

        // onOpenChange should still be called so the parent knows about the dismiss intent
        expect(handleOpenChange).toHaveBeenCalledWith(false, expect.anything());

        // The controlled reopen happens in rAF outside fireEvent's implicit act scope.
        // Wrap the frame wait in act to avoid React act warnings.
        await act(async () => {
          await waitSingleFrame();
        });

        // The drawer should remain open without data-swipe-dismiss
        expect(popup).not.toHaveAttribute('data-swipe-dismiss');
        expect(backdrop).not.toHaveAttribute('data-swipe-dismiss');
        expect(popup).not.toHaveAttribute('data-ending-style');
        expect(popup).toHaveAttribute('data-open', '');
      } finally {
        env.cleanup();
      }
    },
  );

  it.skipIf(isJSDOM)(
    'does not restore snap point when a controlled swipe close is accepted by the parent',
    async () => {
      const env = setupSwipeTestEnv();

      try {
        await render(<ControlledSwipeCloseSnapPointCase />);
        await flushMicrotasks();

        const viewport = screen.getByTestId('viewport');
        const popup = screen.getByTestId('popup');

        env.pointAt(popup);

        await simulateTimedDownSwipe(viewport, 100, 260, 1000, 1010, 1040);
        expect(screen.getByTestId('active-snap').textContent).toBe('100px');
      } finally {
        env.cleanup();
      }
    },
  );

  it.skipIf(isJSDOM)(
    'restores snap point and swipe offsets when swipe close is canceled',
    async () => {
      const env = setupSwipeTestEnv();

      try {
        await render(<CanceledSwipeCloseSnapPointCase />);
        await flushMicrotasks();

        const viewport = screen.getByTestId('viewport');
        const popup = screen.getByTestId('popup');

        env.pointAt(popup);

        await simulateTimedDownSwipe(viewport, 100, 260, 1000, 1010, 1040);

        expect(screen.getByTestId('active-snap').textContent).toBe('100px');
        expect(popup).toHaveAttribute('data-open', '');
        expect(popup).not.toHaveAttribute('data-swipe-dismiss');
        expect(popup).not.toHaveAttribute('data-ending-style');
        expect(popup.style.getPropertyValue('--drawer-swipe-movement-y')).toBe('0px');
      } finally {
        env.cleanup();
      }
    },
  );

  it.skipIf(isJSDOM)(
    'allows dragging past a snap point when snapToSequentialPoints is enabled',
    async () => {
      const env = setupSwipeTestEnv();

      const useFakeTimers = isJSDOM;
      if (useFakeTimers) {
        vi.useFakeTimers();
      }

      try {
        await render(<SnapPointSequentialSkipCase />);
        await flushMicrotasks();

        const viewport = screen.getByTestId('viewport');
        const popup = screen.getByTestId('popup');

        env.pointAt(popup);

        const startTime = 1000;
        const moveTime = 1010;
        const endTime = 1040;

        await simulateTimedDownSwipe(viewport, 500, 50, startTime, moveTime, endTime);

        expect(screen.getByTestId('active-snap').textContent).toBe('1');
      } finally {
        if (useFakeTimers) {
          vi.useRealTimers();
        }
        env.cleanup();
      }
    },
  );

  it.skipIf(isJSDOM)(
    'advances to the next snap point on fast flicks when snapToSequentialPoints is enabled',
    async () => {
      const env = setupSwipeTestEnv();

      const useFakeTimers = isJSDOM;
      if (useFakeTimers) {
        vi.useFakeTimers();
      }

      try {
        await render(<SnapPointSequentialSkipCase />);
        await flushMicrotasks();

        const viewport = screen.getByTestId('viewport');
        const popup = screen.getByTestId('popup');

        env.pointAt(popup);

        const startTime = 2000;
        const moveTime = 2010;
        const endTime = 2050;

        await simulateTimedDownSwipe(viewport, 500, 460, startTime, moveTime, endTime);

        expect(screen.getByTestId('active-snap').textContent).toBe('300px');
      } finally {
        if (useFakeTimers) {
          vi.useRealTimers();
        }
        env.cleanup();
      }
    },
  );

  it.skipIf(isJSDOM)('keeps the drawer open on low-velocity swipes near a snap point', async () => {
    const handleOpenChange = vi.fn();
    const env = setupSwipeTestEnv();

    const useFakeTimers = isJSDOM;
    if (useFakeTimers) {
      vi.useFakeTimers();
    }

    try {
      await render(<SnapPointSwipeCase onOpenChange={handleOpenChange} />);
      await flushMicrotasks();

      const viewport = screen.getByTestId('viewport');
      const popup = screen.getByTestId('popup');

      env.pointAt(popup);

      const startTime = 1000;
      const moveTime = 1005;
      const settleTime = 1015;
      const endTime = 1035;

      await simulateTimedDownSwipe(viewport, 100, 120, startTime, moveTime, endTime, settleTime);

      expect(handleOpenChange).not.toHaveBeenCalledWith(false);
      expect(screen.getByTestId('active-snap').textContent).toBe('100px');
    } finally {
      if (useFakeTimers) {
        vi.useRealTimers();
      }
      env.cleanup();
    }
  });

  it.skipIf(isJSDOM)(
    'keeps the drawer open when the release velocity reverses during an upward swipe',
    async () => {
      const handleOpenChange = vi.fn();
      const env = setupSwipeTestEnv();

      const useFakeTimers = isJSDOM;
      if (useFakeTimers) {
        vi.useFakeTimers();
      }

      try {
        await render(<SnapPointSwipeCase onOpenChange={handleOpenChange} />);
        await flushMicrotasks();

        const viewport = screen.getByTestId('viewport');
        const popup = screen.getByTestId('popup');

        env.pointAt(popup);

        const startTime = 1000;
        const nudgeTime = 1003;
        const peakTime = 1010;
        const reversalTime = 1015;
        const endTime = 1025;

        await simulateTimedSwipe(viewport, [
          { type: 'down', x: 100, y: 300, time: startTime },
          { type: 'move', x: 100, y: 299, time: nudgeTime },
          { type: 'move', x: 100, y: 120, time: peakTime },
          { type: 'move', x: 100, y: 140, time: reversalTime },
          { type: 'up', x: 100, y: 140, time: endTime },
        ]);

        expect(handleOpenChange).not.toHaveBeenCalledWith(false);
      } finally {
        if (useFakeTimers) {
          vi.useRealTimers();
        }
        env.cleanup();
      }
    },
  );

  it('closes when CloseWatcher emits a close event', async () => {
    const handleOpenChange = vi.fn();

    class CloseWatcherStub extends EventTarget {
      static instances: CloseWatcherStub[] = [];
      onclose: ((this: CloseWatcherStub, ev: Event) => void) | null = null;
      oncancel: ((this: CloseWatcherStub, ev: Event) => void) | null = null;
      destroy = vi.fn();
      close = vi.fn();
      requestClose = vi.fn();
      constructor() {
        super();
        CloseWatcherStub.instances.push(this);
      }
    }

    const originalCloseWatcher = (window as Window & { CloseWatcher?: unknown | undefined })
      .CloseWatcher;
    (window as Window & { CloseWatcher?: typeof CloseWatcherStub | undefined }).CloseWatcher =
      CloseWatcherStub;

    try {
      await render(
        <Drawer.Root defaultOpen onOpenChange={handleOpenChange}>
          <Drawer.Portal>
            <Drawer.Viewport>
              <Drawer.Popup>Drawer</Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      await flushMicrotasks();

      const instance = CloseWatcherStub.instances[CloseWatcherStub.instances.length - 1];
      expect(instance).not.toBeUndefined();

      await act(async () => {
        instance.dispatchEvent(new Event('close'));
        await flushMicrotasks();
      });

      expect(handleOpenChange).toHaveBeenCalled();
      const lastCall = handleOpenChange.mock.calls[handleOpenChange.mock.calls.length - 1];
      expect(lastCall?.[0]).toBe(false);
      expect(lastCall?.[1]?.reason).toBe(REASONS.closeWatcher);
    } finally {
      (window as Window & { CloseWatcher?: unknown | undefined }).CloseWatcher =
        originalCloseWatcher;
    }
  });
});

// ---- packages/react/src/drawer/swipe-area/DrawerSwipeArea.test.tsx ----
import { beforeAll, describe, expect, it, vi } from 'vitest';
import { Drawer } from '@base-ui/react/drawer';
import { act, fireEvent, flushMicrotasks, screen, waitFor } from '@mui/internal-test-utils';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';

type Point = {
  x: number;
  y: number;
};

type SwipeInput = 'pointer' | 'touch';

type SwipeOptions = {
  beforeRelease?: (() => Promise<unknown>) | (() => unknown);
  input?: SwipeInput;
  timeStepMs?: number;
  startTimeMs?: number;
};

function createTouch(target: EventTarget, point: { clientX: number; clientY: number }) {
  if (typeof Touch === 'function') {
    return new Touch({
      identifier: 1,
      target,
      ...point,
    });
  }

  return point;
}

async function swipe(element: HTMLElement, start: Point, end: Point, options: SwipeOptions = {}) {
  const stepX = start.x + (end.x === start.x ? 0 : Math.sign(end.x - start.x));
  const stepY = start.y + (end.y === start.y ? 0 : Math.sign(end.y - start.y));
  const { beforeRelease, input = 'pointer', timeStepMs, startTimeMs = 0 } = options;
  const useTimeStamp = input === 'pointer' && typeof timeStepMs === 'number';
  let timeStamp = startTimeMs;

  if (input === 'touch') {
    fireEvent.touchStart(element, {
      bubbles: true,
      touches: [
        createTouch(element, {
          clientX: start.x,
          clientY: start.y,
        }),
      ],
    });

    await flushMicrotasks();

    fireEvent.touchMove(element, {
      bubbles: true,
      touches: [
        createTouch(element, {
          clientX: stepX,
          clientY: stepY,
        }),
      ],
    });

    await flushMicrotasks();

    fireEvent.touchMove(element, {
      bubbles: true,
      touches: [
        createTouch(element, {
          clientX: end.x,
          clientY: end.y,
        }),
      ],
    });

    await flushMicrotasks();

    if (beforeRelease) {
      await beforeRelease();
      await flushMicrotasks();
    }

    fireEvent.touchEnd(element, {
      bubbles: true,
      changedTouches: [
        createTouch(element, {
          clientX: end.x,
          clientY: end.y,
        }),
      ],
    });

    await flushMicrotasks();
    return;
  }

  fireEvent.pointerDown(element, {
    button: 0,
    buttons: 1,
    pointerId: 1,
    clientX: start.x,
    clientY: start.y,
    pointerType: 'mouse',
    ...(useTimeStamp ? { timeStamp } : null),
  });

  await flushMicrotasks();

  if (useTimeStamp) {
    timeStamp += timeStepMs;
  }

  fireEvent.pointerMove(element, {
    pointerId: 1,
    clientX: stepX,
    clientY: stepY,
    pointerType: 'mouse',
    ...(useTimeStamp ? { timeStamp } : null),
  });

  await flushMicrotasks();

  if (useTimeStamp) {
    timeStamp += timeStepMs;
  }

  fireEvent.pointerMove(element, {
    pointerId: 1,
    clientX: end.x,
    clientY: end.y,
    pointerType: 'mouse',
    ...(useTimeStamp ? { timeStamp } : null),
  });

  await flushMicrotasks();

  if (beforeRelease) {
    await beforeRelease();
    await flushMicrotasks();
  }

  if (useTimeStamp) {
    timeStamp += timeStepMs;
  }

  fireEvent.pointerUp(element, {
    pointerId: 1,
    clientX: end.x,
    clientY: end.y,
    pointerType: 'mouse',
    ...(useTimeStamp ? { timeStamp } : null),
  });

  await flushMicrotasks();
}

function wait(ms: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });
}

function nextMacrotask() {
  return wait(0);
}

async function swipeUp(element: HTMLElement, startY: number, endY: number, options?: SwipeOptions) {
  return swipe(element, { x: 10, y: startY }, { x: 10, y: endY }, options);
}

async function swipeLeft(
  element: HTMLElement,
  startX: number,
  endX: number,
  options?: SwipeOptions,
) {
  return swipe(element, { x: startX, y: 10 }, { x: endX, y: 10 }, options);
}

describe('<Drawer.SwipeArea />', () => {
  beforeAll(function beforeHook() {
    // PointerEvent not fully implemented in jsdom, causing fireEvent.pointer* to ignore options.
    // https://github.com/jsdom/jsdom/issues/2527
    (window as any).PointerEvent = window.MouseEvent;
  });

  const { render } = createRenderer();

  describeConformance(<Drawer.SwipeArea />, () => ({
    refInstanceof: window.HTMLDivElement,
    render(node) {
      return render(<Drawer.Root>{node}</Drawer.Root>);
    },
  }));

  it('opens the drawer when swiped in the open direction', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    expect(swipeArea).toHaveAttribute('data-closed', '');

    await swipeUp(swipeArea, 120, 40);

    expect(swipeArea).toHaveAttribute('data-open', '');
  });

  it('does not open when the swipe direction never locks to the open direction', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root onOpenChange={handleOpenChange}>
        <Drawer.SwipeArea data-testid="swipe-area" />
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    await swipe(swipeArea, { x: 10, y: 120 }, { x: 70, y: 118 });

    expect(swipeArea).toHaveAttribute('data-closed', '');
    expect(handleOpenChange).not.toHaveBeenCalled();
  });

  it('prevents default pointer down for non-touch swipes', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
      </Drawer.Root>,
    );

    const notCancelled = fireEvent.pointerDown(screen.getByTestId('swipe-area'), {
      button: 0,
      buttons: 1,
      pointerId: 1,
      clientX: 10,
      clientY: 120,
      pointerType: 'mouse',
    });

    expect(notCancelled).toBe(false);
  });

  it('does not open the drawer when disabled', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" disabled />
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    await swipeUp(swipeArea, 120, 40);

    expect(swipeArea).toHaveAttribute('data-closed', '');
  });

  it('respects custom swipeDirection', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" swipeDirection="left" />
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    await swipeLeft(swipeArea, 120, 40);

    expect(swipeArea).toHaveAttribute('data-open', '');
  });

  it('opens the drawer when swiped with touch events', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    await swipeUp(swipeArea, 120, 40, { input: 'touch' });

    expect(swipeArea).toHaveAttribute('data-open', '');
    expect(screen.getByTestId('popup')).toHaveAttribute('data-open', '');
  });

  it('applies data-swiping during an active swipe gesture', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    await swipeUp(swipeArea, 120, 40, {
      beforeRelease() {
        expect(swipeArea).toHaveAttribute('data-swiping', '');
      },
    });

    expect(swipeArea).not.toHaveAttribute('data-swiping');
  });

  it('re-enables outside press dismissal after opening by swipe', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    await swipeUp(swipeArea, 120, 40, { input: 'touch' });

    expect(screen.getByTestId('popup')).toHaveAttribute('data-open', '');

    await act(async () => {
      await nextMacrotask();
    });

    fireEvent.click(document.body);

    await waitFor(() => {
      expect(screen.queryByTestId('popup')).toBe(null);
    });

    expect(swipeArea).toHaveAttribute('data-closed', '');
  });

  it('re-enables outside press dismissal after an interrupted swipe-open gesture', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    fireEvent.pointerDown(swipeArea, {
      button: 0,
      buttons: 1,
      pointerId: 1,
      clientX: 10,
      clientY: 120,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    fireEvent.pointerMove(swipeArea, {
      pointerId: 1,
      clientX: 10,
      clientY: 119,
      buttons: 1,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    fireEvent.pointerMove(swipeArea, {
      pointerId: 1,
      clientX: 10,
      clientY: 80,
      buttons: 1,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    expect(screen.getByTestId('popup')).toHaveAttribute('data-open', '');
    expect(swipeArea).toHaveAttribute('data-open', '');

    fireEvent.pointerMove(swipeArea, {
      pointerId: 1,
      clientX: 10,
      clientY: 60,
      buttons: 2,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    await act(async () => {
      await nextMacrotask();
    });

    fireEvent.click(document.body);

    await waitFor(() => {
      expect(screen.queryByTestId('popup')).toBe(null);
    });

    expect(swipeArea).toHaveAttribute('data-closed', '');
  });

  it('re-enables outside press dismissal after a context menu interrupts swipe-open', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');

    fireEvent.pointerDown(swipeArea, {
      button: 0,
      buttons: 1,
      pointerId: 1,
      clientX: 10,
      clientY: 120,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    fireEvent.pointerMove(swipeArea, {
      pointerId: 1,
      clientX: 10,
      clientY: 119,
      buttons: 1,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    fireEvent.pointerMove(swipeArea, {
      pointerId: 1,
      clientX: 10,
      clientY: 80,
      buttons: 1,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    expect(screen.getByTestId('popup')).toHaveAttribute('data-open', '');

    fireEvent.pointerMove(swipeArea, {
      pointerId: 1,
      clientX: 10,
      clientY: 60,
      buttons: 2,
      pointerType: 'mouse',
    });

    await flushMicrotasks();

    fireEvent.contextMenu(swipeArea, {
      button: 2,
      clientX: 10,
      clientY: 60,
    });

    await act(async () => {
      await nextMacrotask();
    });

    fireEvent.click(document.body);

    await waitFor(() => {
      expect(screen.queryByTestId('popup')).toBe(null);
    });
  });

  it.skipIf(isJSDOM)('uses a size-based swipe threshold by default', async () => {
    await render(
      <Drawer.Root>
        <Drawer.SwipeArea data-testid="swipe-area" />
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup" style={{ height: 200 }}>
              Drawer
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const swipeArea = screen.getByTestId('swipe-area');
    const slowSwipe = {
      async beforeRelease() {
        const popup = await screen.findByTestId('popup');
        Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });
        // Age the last drag sample past the flick-velocity window so distance decides the outcome.
        await act(async () => {
          await wait(81);
        });
      },
    };

    await swipeUp(swipeArea, 200, 130, slowSwipe);

    expect(swipeArea).toHaveAttribute('data-closed', '');

    await swipeUp(swipeArea, 200, 80, slowSwipe);

    expect(swipeArea).toHaveAttribute('data-open', '');
  });
});

// ---- packages/react/src/drawer/viewport/DrawerViewport.test.tsx ----
import { beforeAll, describe, expect, it, vi } from 'vitest';
import * as ReactDOM from 'react-dom';
import { Combobox } from '@base-ui/react/combobox';
import { Drawer } from '@base-ui/react/drawer';
import { Slider } from '@base-ui/react/slider';
import { fireEvent, flushMicrotasks, screen, waitFor } from '@mui/internal-test-utils';
import { createRenderer, isJSDOM } from '#test-utils';

describe('<Drawer.Viewport />', () => {
  beforeAll(function beforeHook() {
    // PointerEvent not fully implemented in jsdom, causing fireEvent.pointer* to ignore options.
    // https://github.com/jsdom/jsdom/issues/2527
    (window as any).PointerEvent = window.MouseEvent;
  });

  const { render } = createRenderer();

  function createTouch(target: EventTarget, point: { clientX: number; clientY: number }) {
    if (typeof Touch === 'function') {
      return new Touch({
        identifier: 1,
        target,
        ...point,
      });
    }

    return point;
  }

  function createNativeTouchMove(target: EventTarget, point: { clientX: number; clientY: number }) {
    const touchMove = new Event('touchmove', { bubbles: true, cancelable: true });
    Object.defineProperty(touchMove, 'touches', {
      value: [createTouch(target, point)],
      configurable: true,
    });
    return touchMove;
  }

  it('clears text selection on swipe start', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              <Drawer.Content>
                <span data-testid="text">Selectable</span>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const text = screen.getByTestId('text');
    expect(text.firstChild).toBeTruthy();

    const selection = window.getSelection();
    expect(selection).not.toBeNull();
    if (!selection || !text.firstChild) {
      return;
    }

    const range = document.createRange();
    range.setStart(text.firstChild, 0);
    range.setEnd(text.firstChild, 5);
    selection.removeAllRanges();
    selection.addRange(range);
    expect(selection.isCollapsed).toBe(false);

    const popup = screen.getByTestId('popup');
    const viewport = screen.getByTestId('viewport');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.pointerDown(viewport, {
        button: 0,
        buttons: 1,
        pointerId: 1,
        clientX: 0,
        clientY: 0,
        pointerType: 'mouse',
      });
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(selection.rangeCount).toBe(0);
  });

  it('does not clear text selection on touch swipe start', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              <Drawer.Content>
                <span data-testid="text">Selectable</span>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const text = screen.getByTestId('text');
    expect(text.firstChild).toBeTruthy();

    const selection = window.getSelection();
    expect(selection).not.toBeNull();
    if (!selection || !text.firstChild) {
      return;
    }

    const range = document.createRange();
    range.setStart(text.firstChild, 0);
    range.setEnd(text.firstChild, 5);
    selection.removeAllRanges();
    selection.addRange(range);
    expect(selection.isCollapsed).toBe(false);

    const popup = screen.getByTestId('popup');
    const viewport = screen.getByTestId('viewport');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.touchStart(viewport, {
        touches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(selection.rangeCount).toBe(1);
  });

  it('starts touch swipes from interactive elements', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              <button type="button" data-testid="button">
                Action
              </button>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const button = screen.getByTestId('button');
    const backdrop = screen.getByTestId('backdrop');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => button;

    try {
      fireEvent.touchStart(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('allows clicks on non-interactive elements without data-base-ui-swipe-ignore', async () => {
    const handleClick = vi.fn();
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange}>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <Drawer.Content>
                <div data-testid="target" onClick={handleClick}>
                  Action
                </div>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const target = screen.getByTestId('target');
    const backdrop = screen.getByTestId('backdrop');
    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => target;

    try {
      fireEvent.touchStart(target, {
        touches: [
          createTouch(target, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });
      fireEvent.pointerDown(target, { pointerType: 'touch' });
      fireEvent.touchEnd(target, {
        changedTouches: [
          createTouch(target, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });
      fireEvent.click(target, { detail: 1 });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleOpenChange).not.toHaveBeenCalled();
    expect(backdrop).not.toHaveAttribute('data-swiping');
  });

  it('does not start touch swipes from elements with data-base-ui-swipe-ignore', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange}>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup>
              <Drawer.Content>
                <div data-testid="target" data-base-ui-swipe-ignore>
                  Action
                </div>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const target = screen.getByTestId('target');
    const backdrop = screen.getByTestId('backdrop');

    fireEvent.touchStart(target, {
      touches: [
        createTouch(target, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    fireEvent.touchMove(target, {
      touches: [
        createTouch(target, {
          clientX: 0,
          clientY: 40,
        }),
      ],
    });

    fireEvent.touchEnd(target, {
      changedTouches: [
        createTouch(target, {
          clientX: 0,
          clientY: 40,
        }),
      ],
    });

    await flushMicrotasks();

    expect(backdrop).not.toHaveAttribute('data-swiping');
    expect(handleOpenChange).not.toHaveBeenCalled();
  });

  it('does not prevent native touch scrolling in portaled descendants', async () => {
    const portalContainer = document.createElement('div');
    document.body.append(portalContainer);

    function PortaledPopup() {
      return ReactDOM.createPortal(
        <div data-testid="portaled-popup">Portaled popup</div>,
        portalContainer,
      );
    }

    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup>
              <Drawer.Content>Content</Drawer.Content>
              <PortaledPopup />
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const portaledPopup = screen.getByTestId('portaled-popup');
    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => portaledPopup;

    try {
      fireEvent.touchStart(portaledPopup, {
        touches: [
          createTouch(portaledPopup, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      const touchMove = createNativeTouchMove(portaledPopup, {
        clientX: 0,
        clientY: 40,
      });
      portaledPopup.dispatchEvent(touchMove);

      expect(touchMove.defaultPrevented).toBe(false);
    } finally {
      document.elementFromPoint = originalElementFromPoint;
      portalContainer.remove();
    }
  });

  it.skipIf(isJSDOM)(
    'allows touch gestures on a portaled combobox popup without starting drawer swipe',
    async () => {
      const handleOpenChange = vi.fn();
      const { user } = await render(
        <Drawer.Root open onOpenChange={handleOpenChange}>
          <Drawer.Portal>
            <Drawer.Backdrop data-testid="backdrop" />
            <Drawer.Viewport>
              <Drawer.Popup>
                <Drawer.Content>
                  <Combobox.Root
                    defaultOpen
                    items={[
                      'Apple',
                      'Banana',
                      'Cherry',
                      'Date',
                      'Elderberry',
                      'Fig',
                      'Grape',
                      'Honeydew',
                      'Kiwi',
                      'Lime',
                    ]}
                  >
                    <Combobox.Input />
                    <Combobox.Portal>
                      <Combobox.Positioner>
                        <Combobox.Popup>
                          <Combobox.List style={{ maxHeight: 40, overflow: 'auto' }}>
                            {(item: string) => (
                              <Combobox.Item key={item} value={item}>
                                {item}
                              </Combobox.Item>
                            )}
                          </Combobox.List>
                        </Combobox.Popup>
                      </Combobox.Positioner>
                    </Combobox.Portal>
                  </Combobox.Root>
                </Drawer.Content>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const listbox = await screen.findByRole('listbox');
      const backdrop = screen.getByTestId('backdrop');
      await waitFor(() => {
        expect(listbox.scrollHeight).toBeGreaterThan(listbox.clientHeight);
      });
      expect(listbox.scrollHeight).toBeGreaterThan(listbox.clientHeight);

      const originalElementFromPoint = document.elementFromPoint;
      document.elementFromPoint = () => listbox;

      try {
        const rect = listbox.getBoundingClientRect();

        await user.pointer([
          {
            target: listbox,
            coords: {
              clientX: rect.left + rect.width / 2,
              clientY: rect.top + rect.height - 8,
            },
            keys: '[TouchA>]',
          },
          {
            target: listbox,
            coords: {
              clientX: rect.left + rect.width / 2,
              clientY: rect.top + rect.height / 2,
            },
            pointerName: 'TouchA',
          },
          {
            target: listbox,
            coords: {
              clientX: rect.left + rect.width / 2,
              clientY: rect.top + 8,
            },
            pointerName: 'TouchA',
          },
          { keys: '[/TouchA]' },
        ]);

        expect(backdrop).not.toHaveAttribute('data-swiping');
        expect(handleOpenChange).not.toHaveBeenCalled();
        expect(listbox).toBeVisible();
      } finally {
        document.elementFromPoint = originalElementFromPoint;
      }
    },
  );

  it('still allows touch swipes from elements with legacy data-swipe-ignore', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange} swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup>
              <div data-testid="target" data-swipe-ignore>
                Action
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const target = screen.getByTestId('target');
    const backdrop = screen.getByTestId('backdrop');
    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => target;

    try {
      fireEvent.touchStart(target, {
        touches: [
          createTouch(target, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(target, {
        touches: [
          createTouch(target, {
            clientX: 0,
            clientY: 40,
          }),
        ],
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');

      fireEvent.touchEnd(target, {
        changedTouches: [
          createTouch(target, {
            clientX: 0,
            clientY: 80,
          }),
        ],
      });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
    expect(handleOpenChange).not.toHaveBeenCalled();
  });

  it('does not start non-touch swipes from Drawer.Content', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <Drawer.Content>
                <div data-testid="target">Action</div>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const target = screen.getByTestId('target');
    const backdrop = screen.getByTestId('backdrop');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => target;

    try {
      fireEvent.pointerDown(target, {
        button: 0,
        buttons: 1,
        pointerId: 1,
        clientX: 0,
        clientY: 0,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      expect(backdrop).not.toHaveAttribute('data-swiping');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('does not jump when touch starts outside the popup and then enters it', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              <Drawer.Content>Content</Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const viewport = screen.getByTestId('viewport');
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');
    Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = (_x, y) => (y < 100 ? viewport : popup);

    try {
      fireEvent.touchStart(viewport, {
        touches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(viewport, {
        touches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 120,
          }),
        ],
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');
      expect(Number.parseFloat(popup.style.getPropertyValue('--drawer-swipe-movement-y'))).toBe(0);
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('dismisses when touch starts outside the popup, then continues swiping down inside it', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange} swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">
              <Drawer.Content>Content</Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const viewport = screen.getByTestId('viewport');
    const popup = screen.getByTestId('popup');
    Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = (_x, y) => (y < 100 ? viewport : popup);

    try {
      fireEvent.touchStart(viewport, {
        touches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(viewport, {
        touches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 120,
          }),
        ],
      });

      fireEvent.touchMove(viewport, {
        touches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 170,
          }),
        ],
      });

      fireEvent.touchEnd(viewport, {
        changedTouches: [
          createTouch(viewport, {
            clientX: 0,
            clientY: 170,
          }),
        ],
      });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(handleOpenChange).toHaveBeenCalledWith(
      false,
      expect.objectContaining({ reason: 'swipe' }),
    );
  });

  it('treats pen interactions on Drawer.Content as non-touch swipes', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup>
              <Drawer.Content>
                <button type="button" data-testid="button">
                  Action
                </button>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const button = screen.getByTestId('button');
    const backdrop = screen.getByTestId('backdrop');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => button;

    try {
      const pointerDownEvent = new Event('pointerdown', {
        bubbles: true,
        cancelable: true,
      }) as PointerEvent;

      Object.defineProperties(pointerDownEvent, {
        button: { value: 0 },
        buttons: { value: 1 },
        pointerId: { value: 1 },
        pointerType: { value: 'pen' },
        clientX: { value: 0 },
        clientY: { value: 0 },
      });

      fireEvent(button, pointerDownEvent);

      fireEvent.touchStart(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(backdrop).not.toHaveAttribute('data-swiping');

      const prevented = fireEvent.touchMove(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 10,
          }),
        ],
      });

      expect(prevented).toBe(true);
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('does not mark nested drawers as swiping until movement passes the threshold', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Viewport data-testid="parent-viewport">
            <Drawer.Popup data-testid="parent-popup">
              <Drawer.Root open swipeDirection="down">
                <Drawer.Portal>
                  <Drawer.Viewport data-testid="child-viewport">
                    <Drawer.Popup data-testid="child-popup">
                      <button type="button" data-testid="child-button">
                        Action
                      </button>
                    </Drawer.Popup>
                  </Drawer.Viewport>
                </Drawer.Portal>
              </Drawer.Root>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const parentPopup = screen.getByTestId('parent-popup');
    const childPopup = screen.getByTestId('child-popup');
    const parentViewport = screen.getByTestId('parent-viewport');
    const childViewport = screen.getByTestId('child-viewport');
    const button = screen.getByTestId('child-button');
    Object.defineProperty(childPopup, 'offsetHeight', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => childPopup;

    try {
      fireEvent.touchStart(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(parentViewport).not.toHaveAttribute('data-nested-dialog-open');
      expect(childViewport).not.toHaveAttribute('data-nested-dialog-open');
      expect(parentPopup).not.toHaveAttribute('data-nested-drawer-swiping');

      fireEvent.touchMove(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 5,
          }),
        ],
      });

      fireEvent.touchMove(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 20,
          }),
        ],
      });

      await flushMicrotasks();

      expect(parentPopup).toHaveAttribute('data-nested-drawer-swiping', '');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('clears nested swiping when a nested drawer swipe is reversed before release', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="parent-popup">
              <Drawer.Root open swipeDirection="down">
                <Drawer.Portal>
                  <Drawer.Viewport>
                    <Drawer.Popup data-testid="child-popup">
                      <button type="button" data-testid="child-button">
                        Action
                      </button>
                    </Drawer.Popup>
                  </Drawer.Viewport>
                </Drawer.Portal>
              </Drawer.Root>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const parentPopup = screen.getByTestId('parent-popup');
    const childPopup = screen.getByTestId('child-popup');
    const button = screen.getByTestId('child-button');
    Object.defineProperty(childPopup, 'offsetHeight', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => childPopup;

    try {
      fireEvent.touchStart(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      fireEvent.touchMove(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 5,
          }),
        ],
      });

      fireEvent.touchMove(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 20,
          }),
        ],
      });

      await flushMicrotasks();

      expect(parentPopup).toHaveAttribute('data-nested-drawer-swiping', '');

      fireEvent.touchMove(button, {
        touches: [
          createTouch(button, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(parentPopup).not.toHaveAttribute('data-nested-drawer-swiping');
      expect(parentPopup.style.getPropertyValue('--drawer-swipe-progress')).toBe('0');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('prevents touchmove at scroll top when swiping down on scrollable content', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 0;

    fireEvent.touchStart(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    const prevented = fireEvent.touchMove(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 10,
        }),
      ],
    });

    expect(prevented).toBe(false);
  });

  it('prevents touchmove at scroll bottom when swiping up on scrollable content', async () => {
    await render(
      <Drawer.Root open swipeDirection="up">
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 80;

    fireEvent.touchStart(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 20,
        }),
      ],
    });

    const prevented = fireEvent.touchMove(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 10,
        }),
      ],
    });

    expect(prevented).toBe(false);
  });

  it('prevents touchmove when a scrollable ancestor wraps the popup at the top', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Viewport>
            <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
              <Drawer.Popup>
                <Drawer.Content>
                  <span data-testid="item">Scrollable content</span>
                </Drawer.Content>
              </Drawer.Popup>
            </div>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 0;

    const item = screen.getByTestId('item');

    fireEvent.touchStart(item, {
      touches: [
        createTouch(item, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    const prevented = fireEvent.touchMove(item, {
      touches: [
        createTouch(item, {
          clientX: 0,
          clientY: 10,
        }),
      ],
    });

    expect(prevented).toBe(false);
  });

  it('prevents touchmove when there is no scroll container', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <Drawer.Content>Content</Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const popup = screen.getByTestId('popup');

    fireEvent.touchStart(popup, {
      touches: [
        createTouch(popup, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    const prevented = fireEvent.touchMove(popup, {
      touches: [
        createTouch(popup, {
          clientX: 0,
          clientY: 10,
        }),
      ],
    });

    expect(prevented).toBe(false);
  });

  it('does not block touchmove on native range inputs', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <input type="range" data-testid="range" />
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const range = screen.getByTestId('range');
    const backdrop = screen.getByTestId('backdrop');

    fireEvent.touchStart(range, {
      touches: [
        createTouch(range, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    const dispatched = fireEvent.touchMove(range, {
      touches: [
        createTouch(range, {
          clientX: 20,
          clientY: 0,
        }),
      ],
    });

    await waitFor(() => {
      expect(dispatched).toBe(true);
      expect(backdrop).not.toHaveAttribute('data-swiping');
    });
  });

  it('does not block touchmove on slider thumb range inputs', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <Slider.Root defaultValue={50}>
                <Slider.Control>
                  <Slider.Track>
                    <Slider.Indicator />
                    <Slider.Thumb />
                  </Slider.Track>
                </Slider.Control>
              </Slider.Root>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const sliderInput = screen.getByRole('slider');
    const backdrop = screen.getByTestId('backdrop');

    fireEvent.touchStart(sliderInput, {
      touches: [
        createTouch(sliderInput, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    const dispatched = fireEvent.touchMove(sliderInput, {
      touches: [
        createTouch(sliderInput, {
          clientX: 20,
          clientY: 0,
        }),
      ],
    });

    await flushMicrotasks();

    expect(dispatched).toBe(true);
    expect(backdrop).not.toHaveAttribute('data-swiping');
  });

  it('does not start swiping when adjusting input selection handles', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <input data-testid="input" defaultValue="Selectable text" />
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const input = screen.getByTestId('input') as HTMLInputElement;
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');

    input.focus();
    input.setSelectionRange(0, 5);

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.touchStart(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).not.toHaveAttribute('data-swiping');

      const dispatched = fireEvent.touchMove(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 10,
          }),
        ],
      });

      await waitFor(() => {
        expect(dispatched).toBe(true);
        expect(backdrop).not.toHaveAttribute('data-swiping');
      });
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('does not start swiping when adjusting textarea selection handles', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <textarea data-testid="textarea" defaultValue="Selectable text" />
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement;
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');

    textarea.focus();
    textarea.setSelectionRange(0, 5);

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.touchStart(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).not.toHaveAttribute('data-swiping');

      const dispatched = fireEvent.touchMove(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 10,
          }),
        ],
      });

      await waitFor(() => {
        expect(dispatched).toBe(true);
        expect(backdrop).not.toHaveAttribute('data-swiping');
      });
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('does not start swiping when adjusting contenteditable selection handles', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <div contentEditable suppressContentEditableWarning data-testid="editable">
                Selectable text
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const editable = screen.getByTestId('editable');
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');
    const selection = window.getSelection();
    expect(selection).not.toBeNull();
    expect(editable.firstChild).toBeTruthy();
    if (!selection || !editable.firstChild) {
      return;
    }

    editable.focus();
    const range = document.createRange();
    range.setStart(editable.firstChild, 0);
    range.setEnd(editable.firstChild, 5);
    selection.removeAllRanges();
    selection.addRange(range);

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.touchStart(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).not.toHaveAttribute('data-swiping');

      const dispatched = fireEvent.touchMove(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 10,
          }),
        ],
      });

      await waitFor(() => {
        expect(dispatched).toBe(true);
        expect(backdrop).not.toHaveAttribute('data-swiping');
      });
    } finally {
      document.elementFromPoint = originalElementFromPoint;
      selection.removeAllRanges();
    }
  });

  it('does not start swiping when adjusting regular text selection handles', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <span data-testid="text">Selectable text</span>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const text = screen.getByTestId('text');
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');
    const selection = window.getSelection();
    expect(selection).not.toBeNull();
    expect(text.firstChild).toBeTruthy();
    if (!selection || !text.firstChild) {
      return;
    }

    const range = document.createRange();
    range.setStart(text.firstChild, 0);
    range.setEnd(text.firstChild, 5);
    selection.removeAllRanges();
    selection.addRange(range);

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.touchStart(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).not.toHaveAttribute('data-swiping');

      const dispatched = fireEvent.touchMove(popup, {
        touches: [
          createTouch(popup, {
            clientX: 0,
            clientY: 10,
          }),
        ],
      });

      await waitFor(() => {
        expect(dispatched).toBe(true);
        expect(backdrop).not.toHaveAttribute('data-swiping');
      });
    } finally {
      document.elementFromPoint = originalElementFromPoint;
      selection.removeAllRanges();
    }
  });

  it('allows touchmove when scrolling down from scroll top', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 0;

    fireEvent.touchStart(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 0,
        }),
      ],
    });

    const prevented = fireEvent.touchMove(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: -10,
        }),
      ],
    });

    expect(prevented).toBe(true);
  });

  it('does not start an opposite-direction swipe from scroll bottom for down drawers with snap points', async () => {
    await render(
      <Drawer.Root open swipeDirection="down" snapPoints={['100px', 1]}>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 80;

    fireEvent.touchStart(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 40,
        }),
      ],
    });

    const moveAllowed = fireEvent.touchMove(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 0,
          clientY: 20,
        }),
      ],
    });

    await flushMicrotasks();

    expect(moveAllowed).toBe(true);
    expect(backdrop).not.toHaveAttribute('data-swiping');
  });

  it('does not start an opposite-direction swipe from scroll right edge for right drawers', async () => {
    await render(
      <Drawer.Root open swipeDirection="right">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowX: 'auto', maxWidth: 40 }}>
                <div style={{ width: 120, height: 40 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    Object.defineProperty(scroll, 'scrollWidth', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientWidth', { value: 40, configurable: true });
    scroll.scrollLeft = 80;

    fireEvent.touchStart(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 40,
          clientY: 0,
        }),
      ],
    });

    const moveAllowed = fireEvent.touchMove(scroll, {
      touches: [
        createTouch(scroll, {
          clientX: 20,
          clientY: 0,
        }),
      ],
    });

    await flushMicrotasks();

    expect(moveAllowed).toBe(true);
    expect(backdrop).not.toHaveAttribute('data-swiping');
  });

  it('starts swipe-to-dismiss after a scrollable container reaches the dismiss edge', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 30;

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 30,
          }),
        ],
      });

      const firstMovePrevented = fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 40,
          }),
        ],
      });

      expect(firstMovePrevented).toBe(true);
      expect(backdrop).not.toHaveAttribute('data-swiping');

      scroll.scrollTop = 0;

      const secondMovePrevented = fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 50,
          }),
        ],
      });

      expect(secondMovePrevented).toBe(false);

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('dismisses from a top-edge scroll container with a touch swipe down', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange} swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    const popup = screen.getByTestId('popup');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 0;

    Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 140,
          }),
        ],
      });

      expect(backdrop).toHaveAttribute('data-swiping', '');

      fireEvent.touchEnd(scroll, {
        changedTouches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 140,
          }),
        ],
      });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(handleOpenChange).toHaveBeenCalledWith(
      false,
      expect.objectContaining({ reason: 'swipe' }),
    );
  });

  it('dismisses from a bottom-edge scroll container with a touch swipe up', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange} swipeDirection="up">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    const popup = screen.getByTestId('popup');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 80;

    Object.defineProperty(popup, 'offsetHeight', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 140,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).toHaveAttribute('data-swiping', '');

      fireEvent.touchEnd(scroll, {
        changedTouches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(handleOpenChange).toHaveBeenCalledWith(
      false,
      expect.objectContaining({ reason: 'swipe' }),
    );
  });

  it('dismisses from a left-edge horizontal scroll container with a touch swipe right', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange} swipeDirection="right">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <div data-testid="scroll" style={{ overflowX: 'auto', maxWidth: 40 }}>
                <div style={{ width: 120, height: 40 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    const popup = screen.getByTestId('popup');
    Object.defineProperty(scroll, 'scrollWidth', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientWidth', { value: 40, configurable: true });
    scroll.scrollLeft = 0;

    Object.defineProperty(popup, 'offsetWidth', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 140,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).toHaveAttribute('data-swiping', '');

      fireEvent.touchEnd(scroll, {
        changedTouches: [
          createTouch(scroll, {
            clientX: 140,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(handleOpenChange).toHaveBeenCalledWith(
      false,
      expect.objectContaining({ reason: 'swipe' }),
    );
  });

  it('dismisses from a right-edge horizontal scroll container with a touch swipe left', async () => {
    const handleOpenChange = vi.fn();

    await render(
      <Drawer.Root open onOpenChange={handleOpenChange} swipeDirection="left">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup data-testid="popup">
              <div data-testid="scroll" style={{ overflowX: 'auto', maxWidth: 40 }}>
                <div style={{ width: 120, height: 40 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    const popup = screen.getByTestId('popup');
    Object.defineProperty(scroll, 'scrollWidth', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientWidth', { value: 40, configurable: true });
    scroll.scrollLeft = 80;

    Object.defineProperty(popup, 'offsetWidth', { value: 200, configurable: true });

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 140,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      expect(backdrop).toHaveAttribute('data-swiping', '');

      fireEvent.touchEnd(scroll, {
        changedTouches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }

    expect(handleOpenChange).toHaveBeenCalledWith(
      false,
      expect.objectContaining({ reason: 'swipe' }),
    );
  });

  it('allows horizontal swipe dismiss from a vertical scroll container', async () => {
    await render(
      <Drawer.Root open swipeDirection="right">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowY: 'auto', maxHeight: 40 }}>
                <div style={{ height: 120 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
    scroll.scrollTop = 20;

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 20,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 20,
            clientY: 20,
          }),
        ],
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('does not lock vertical swipe after minor cross-axis jitter in down drawers', async () => {
    await render(
      <Drawer.Root open swipeDirection="down">
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport>
            <Drawer.Popup>
              <div data-testid="scroll" style={{ overflowX: 'auto', width: 40 }}>
                <div style={{ width: 120, height: 40 }}>Scrollable content</div>
              </div>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const scroll = screen.getByTestId('scroll');
    const backdrop = screen.getByTestId('backdrop');
    Object.defineProperty(scroll, 'scrollWidth', { value: 120, configurable: true });
    Object.defineProperty(scroll, 'clientWidth', { value: 40, configurable: true });
    scroll.scrollLeft = 0;

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => scroll;

    try {
      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 4,
            clientY: 3,
          }),
        ],
      });

      fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 4,
            clientY: 28,
          }),
        ],
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it.skipIf(isJSDOM)(
    'does not hijack cross-axis gestures from mixed-axis scroll containers',
    async () => {
      await render(
        <Drawer.Root open swipeDirection="down">
          <Drawer.Portal>
            <Drawer.Backdrop data-testid="backdrop" />
            <Drawer.Viewport>
              <Drawer.Popup>
                <div data-testid="scroll" style={{ overflow: 'auto', width: 40, height: 40 }}>
                  <div style={{ width: 120, height: 120 }}>Scrollable content</div>
                </div>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const scroll = screen.getByTestId('scroll');
      const backdrop = screen.getByTestId('backdrop');
      Object.defineProperty(scroll, 'scrollHeight', { value: 120, configurable: true });
      Object.defineProperty(scroll, 'clientHeight', { value: 40, configurable: true });
      Object.defineProperty(scroll, 'scrollWidth', { value: 120, configurable: true });
      Object.defineProperty(scroll, 'clientWidth', { value: 40, configurable: true });
      scroll.scrollTop = 0;
      scroll.scrollLeft = 40;

      const originalElementFromPoint = document.elementFromPoint;
      document.elementFromPoint = () => scroll;

      try {
        fireEvent.touchStart(scroll, {
          touches: [
            createTouch(scroll, {
              clientX: 40,
              clientY: 0,
            }),
          ],
        });

        fireEvent.touchMove(scroll, {
          touches: [
            createTouch(scroll, {
              clientX: 10,
              clientY: 20,
            }),
          ],
        });

        await flushMicrotasks();

        expect(backdrop).not.toHaveAttribute('data-swiping');
      } finally {
        document.elementFromPoint = originalElementFromPoint;
      }
    },
  );

  it.skipIf(isJSDOM)(
    'does not block vertical scrolling in right drawers when only vertical overflow exists',
    async () => {
      await render(
        <Drawer.Root open swipeDirection="right">
          <Drawer.Portal>
            <Drawer.Backdrop data-testid="backdrop" />
            <Drawer.Viewport>
              <Drawer.Popup>
                <div data-testid="scroll" style={{ overflowY: 'auto', height: 40 }}>
                  <div style={{ height: 120 }}>Scrollable content</div>
                </div>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const scroll = screen.getByTestId('scroll');
      const backdrop = screen.getByTestId('backdrop');

      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 20,
          }),
        ],
      });

      const dispatched = fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(dispatched).toBe(true);
      expect(backdrop).not.toHaveAttribute('data-swiping');
    },
  );

  it.skipIf(isJSDOM)(
    'does not block vertical scrolling in left drawers when only vertical overflow exists',
    async () => {
      await render(
        <Drawer.Root open swipeDirection="left">
          <Drawer.Portal>
            <Drawer.Backdrop data-testid="backdrop" />
            <Drawer.Viewport>
              <Drawer.Popup>
                <div data-testid="scroll" style={{ overflowY: 'auto', height: 40 }}>
                  <div style={{ height: 120 }}>Scrollable content</div>
                </div>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const scroll = screen.getByTestId('scroll');
      const backdrop = screen.getByTestId('backdrop');

      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 20,
          }),
        ],
      });

      const dispatched = fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(dispatched).toBe(true);
      expect(backdrop).not.toHaveAttribute('data-swiping');
    },
  );

  it.skipIf(isJSDOM)(
    'does not block horizontal scrolling in down drawers when only horizontal overflow exists',
    async () => {
      await render(
        <Drawer.Root open swipeDirection="down">
          <Drawer.Portal>
            <Drawer.Backdrop data-testid="backdrop" />
            <Drawer.Viewport>
              <Drawer.Popup>
                <div data-testid="scroll" style={{ overflowX: 'auto', width: 40 }}>
                  <div style={{ width: 120, height: 40 }}>Scrollable content</div>
                </div>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const scroll = screen.getByTestId('scroll');
      const backdrop = screen.getByTestId('backdrop');

      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 20,
            clientY: 0,
          }),
        ],
      });

      const dispatched = fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(dispatched).toBe(true);
      expect(backdrop).not.toHaveAttribute('data-swiping');
    },
  );

  it.skipIf(isJSDOM)(
    'does not block horizontal scrolling in up drawers when only horizontal overflow exists',
    async () => {
      await render(
        <Drawer.Root open swipeDirection="up">
          <Drawer.Portal>
            <Drawer.Backdrop data-testid="backdrop" />
            <Drawer.Viewport>
              <Drawer.Popup>
                <div data-testid="scroll" style={{ overflowX: 'auto', width: 40 }}>
                  <div style={{ width: 120, height: 40 }}>Scrollable content</div>
                </div>
              </Drawer.Popup>
            </Drawer.Viewport>
          </Drawer.Portal>
        </Drawer.Root>,
      );

      const scroll = screen.getByTestId('scroll');
      const backdrop = screen.getByTestId('backdrop');

      fireEvent.touchStart(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 20,
            clientY: 0,
          }),
        ],
      });

      const dispatched = fireEvent.touchMove(scroll, {
        touches: [
          createTouch(scroll, {
            clientX: 0,
            clientY: 0,
          }),
        ],
      });

      await flushMicrotasks();

      expect(dispatched).toBe(true);
      expect(backdrop).not.toHaveAttribute('data-swiping');
    },
  );

  it('toggles data-swiping on the backdrop while swiping', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const viewport = screen.getByTestId('viewport');
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.pointerDown(viewport, {
        button: 0,
        buttons: 1,
        pointerId: 1,
        clientX: 0,
        clientY: 0,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      fireEvent.pointerMove(viewport, {
        pointerId: 1,
        clientX: 0,
        clientY: 8,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');

      fireEvent.pointerUp(viewport, {
        pointerId: 1,
        clientX: 0,
        clientY: 8,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      expect(backdrop).not.toHaveAttribute('data-swiping');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });

  it('ends swipe drag when the primary mouse button is released mid-gesture', async () => {
    await render(
      <Drawer.Root open>
        <Drawer.Portal>
          <Drawer.Backdrop data-testid="backdrop" />
          <Drawer.Viewport data-testid="viewport">
            <Drawer.Popup data-testid="popup">Drawer</Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>,
    );

    const viewport = screen.getByTestId('viewport');
    const popup = screen.getByTestId('popup');
    const backdrop = screen.getByTestId('backdrop');

    const originalElementFromPoint = document.elementFromPoint;
    document.elementFromPoint = () => popup;

    try {
      fireEvent.pointerDown(viewport, {
        button: 0,
        buttons: 1,
        pointerId: 1,
        clientX: 0,
        clientY: 0,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      fireEvent.pointerMove(viewport, {
        pointerId: 1,
        clientX: 0,
        clientY: 8,
        buttons: 1,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      expect(backdrop).toHaveAttribute('data-swiping', '');

      // Simulate a right-click interruption where the primary button is no longer pressed.
      fireEvent.pointerMove(viewport, {
        pointerId: 1,
        clientX: 0,
        clientY: 12,
        buttons: 2,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      expect(backdrop).not.toHaveAttribute('data-swiping');

      fireEvent.pointerMove(viewport, {
        pointerId: 1,
        clientX: 0,
        clientY: 30,
        buttons: 0,
        pointerType: 'mouse',
      });

      await flushMicrotasks();

      expect(backdrop).not.toHaveAttribute('data-swiping');
    } finally {
      document.elementFromPoint = originalElementFromPoint;
    }
  });
});

