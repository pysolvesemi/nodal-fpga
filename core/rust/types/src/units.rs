use crate::diagnostics::type_error;
use crate::{Code, Diagnostic};

fn overflow(operation: &str, actual: impl ToString, expected: impl ToString) -> Diagnostic {
    type_error(
        Code::Overflow,
        format!("{operation} exceeds its integer representation"),
    )
    .with_actual(actual.to_string())
    .with_expected(expected.to_string())
    .with_remedy("Reduce the quantity or use a supported wider representation before conversion.")
}

macro_rules! scalar {
    ($name:ident) => {
        #[doc = concat!("A checked-arithmetic `u64` ", stringify!($name), ". No implicit unit conversions.")]
        #[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub struct $name(u64);

        impl $name {
            pub const fn new(value: u64) -> Self { Self(value) }
            pub const fn get(self) -> u64 { self.0 }
            pub fn checked_mul(self, factor: u64) -> Result<Self, Diagnostic> {
                self.0.checked_mul(factor).map(Self).ok_or_else(||
                    overflow("multiplication", format!("{} * {factor}", self.0), u64::MAX))
            }
            pub fn to_u32(self) -> Result<u32, Diagnostic> {
                u32::try_from(self.0).map_err(|_| overflow("u32 conversion", self.0, u32::MAX))
            }
            pub fn to_usize(self) -> Result<usize, Diagnostic> {
                usize::try_from(self.0).map_err(|_| overflow("platform-index conversion", self.0, usize::MAX))
            }
        }
    };
}

scalar!(BitCount);
scalar!(BitOffset);
scalar!(ByteLength);
scalar!(ByteOffset);

macro_rules! addition {
    ($left:ident, $right:ident) => {
        impl $left {
            pub fn checked_add(self, amount: $right) -> Result<Self, Diagnostic> {
                self.0.checked_add(amount.get()).map(Self).ok_or_else(|| {
                    overflow(
                        "addition",
                        format!("{} + {}", self.0, amount.get()),
                        u64::MAX,
                    )
                })
            }
        }
    };
}
addition!(BitCount, BitCount);
addition!(BitOffset, BitCount);
addition!(ByteLength, ByteLength);
addition!(ByteOffset, ByteLength);

impl ByteLength {
    pub fn to_bits(self) -> Result<BitCount, Diagnostic> {
        self.checked_mul(8).map(|bytes| BitCount::new(bytes.get()))
    }
}
impl ByteOffset {
    pub fn to_bits(self) -> Result<BitOffset, Diagnostic> {
        self.checked_mul(8).map(|bytes| BitOffset::new(bytes.get()))
    }
}
impl BitCount {
    /// Exact conversion only: partial bytes are rejected, never rounded away.
    pub fn to_bytes_exact(self) -> Result<ByteLength, Diagnostic> {
        require_byte_alignment(self.0)?;
        Ok(ByteLength::new(self.0 / 8))
    }
}
impl BitOffset {
    pub fn to_bytes_exact(self) -> Result<ByteOffset, Diagnostic> {
        require_byte_alignment(self.0)?;
        Ok(ByteOffset::new(self.0 / 8))
    }
}

fn require_byte_alignment(value: u64) -> Result<(), Diagnostic> {
    if !value.is_multiple_of(8) {
        Err(
            type_error(Code::InvalidRange, "bit quantity is not byte-aligned")
                .with_actual(value.to_string())
                .with_expected("a multiple of 8")
                .with_remedy("Keep bit units or provide an explicitly byte-aligned quantity."),
        )
    } else {
        Ok(())
    }
}

macro_rules! range {
    ($name:ident, $offset:ident, $length:ident) => {
        /// A checked half-open interval. Empty ranges are valid and never
        /// overlap. Containment of an empty range includes either boundary.
        #[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub struct $name {
            start: $offset,
            end: $offset,
        }
        impl $name {
            pub fn new(start: $offset, length: $length) -> Result<Self, Diagnostic> {
                Ok(Self {
                    start,
                    end: start.checked_add(length)?,
                })
            }
            pub fn from_bounds(start: $offset, end: $offset) -> Result<Self, Diagnostic> {
                if end < start {
                    return Err(type_error(
                        Code::InvalidRange,
                        "half-open range has reversed endpoints",
                    )
                    .with_actual(format!("[{}, {})", start.get(), end.get()))
                    .with_expected("start <= end")
                    .with_remedy("Supply the endpoints in increasing byte or bit order."));
                }
                Ok(Self { start, end })
            }
            pub const fn start(self) -> $offset {
                self.start
            }
            pub const fn end(self) -> $offset {
                self.end
            }
            pub const fn length(self) -> $length {
                $length::new(self.end.get() - self.start.get())
            }
            pub const fn is_empty(self) -> bool {
                self.start.get() == self.end.get()
            }
            pub const fn contains(self, offset: $offset) -> bool {
                self.start.get() <= offset.get() && offset.get() < self.end.get()
            }
            pub const fn contains_range(self, other: Self) -> bool {
                self.start.get() <= other.start.get() && other.end.get() <= self.end.get()
            }
            pub const fn overlaps(self, other: Self) -> bool {
                !self.is_empty()
                    && !other.is_empty()
                    && self.start.get() < other.end.get()
                    && other.start.get() < self.end.get()
            }
        }
    };
}
range!(BitRange, BitOffset, BitCount);
range!(ByteRange, ByteOffset, ByteLength);

/// Supported logical feature width, from 1 through 64 bits inclusive.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Width(u8);

impl Width {
    pub fn new(value: u64) -> Result<Self, Diagnostic> {
        if !(1..=64).contains(&value) {
            return Err(type_error(Code::Width, "unsupported logical feature width")
                .with_actual(value.to_string())
                .with_expected("1..=64")
                .with_remedy("Use a positive width supported by the 64-bit value profile."));
        }
        // The supported interval above proves this conversion cannot truncate.
        let value = u8::try_from(value).map_err(|_| overflow("width conversion", value, 64))?;
        Ok(Self(value))
    }
    pub const fn get(self) -> u8 {
        self.0
    }
    pub const fn bit_count(self) -> BitCount {
        BitCount::new(self.0 as u64)
    }
    /// Width 64 accepts every `u64`; this never shifts by the operand width.
    pub const fn fits(self, value: u64) -> bool {
        self.0 == 64 || value < (1_u64 << self.0)
    }
}
